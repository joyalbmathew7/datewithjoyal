import os
import razorpay
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import hmac
import hashlib

from django.utils import timezone
from bookings.models import Booking
from .models import Payment


def get_razorpay_client():
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    booking_id = request.data.get("booking_id")

    if not booking_id:
        return Response(
            {"error": "booking_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            booking = get_object_or_404(
                Booking.objects.select_for_update(),
                id=booking_id,
            )

            if booking.status != "PENDING":
                return Response(
                    {"error": "This booking cannot be paid for."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                not booking.hold_expires_at
                or booking.hold_expires_at <= __import__(
                    "django.utils.timezone", fromlist=["now"]
                ).now()
            ):
                return Response(
                    {"error": "The booking hold has expired. Please book again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            amount_paise = int(
                (Decimal(str(booking.total_amount)) * 100)
                .quantize(Decimal("1"))
            )

            if amount_paise < 100:
                return Response(
                    {"error": "The minimum payment amount is ₹1."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Reuse an existing pending order if one is available.
            existing_payment = Payment.objects.filter(
                booking=booking,
                status=Payment.Status.PENDING,
            ).order_by("-created_at").first()

            if existing_payment:
                return Response({
                    "key_id": settings.RAZORPAY_KEY_ID,
                    "order_id": existing_payment.razorpay_order_id,
                    "amount": amount_paise,
                    "currency": existing_payment.currency,
                })

            client = get_razorpay_client()

            order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"booking_{booking.id}",
            })

            Payment.objects.create(
                booking=booking,
                razorpay_order_id=order["id"],
                amount=booking.total_amount,
                currency="INR",
                status=Payment.Status.PENDING,
            )

            return Response({
                "key_id": settings.RAZORPAY_KEY_ID,
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
            }, status=status.HTTP_201_CREATED)

    except razorpay.errors.BadRequestError:
        return Response(
            {"error": "Razorpay rejected the order request."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except razorpay.errors.AuthenticationError:
        return Response(
            {"error": "Razorpay authentication failed. Check backend credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except razorpay.errors.RazorpayError:
        return Response(
            {"error": "Could not create the Razorpay order."},
            status=status.HTTP_502_BAD_GATEWAY,
        )



@api_view(["POST"])
@permission_classes([AllowAny])
def verify_payment(request):
    booking_id = request.data.get("booking_id")
    razorpay_order_id = request.data.get("razorpay_order_id")
    razorpay_payment_id = request.data.get("razorpay_payment_id")
    razorpay_signature = request.data.get("razorpay_signature")

    if not all([
        booking_id,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ]):
        return Response(
            {"error": "All payment verification fields are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                booking_id=booking_id,
                razorpay_order_id=razorpay_order_id,
            )

            booking = Booking.objects.select_for_update().get(
                id=booking_id
            )

            if payment.status == Payment.Status.SUCCESS:
                if payment.razorpay_payment_id == razorpay_payment_id:
                    return Response({
                        "message": "Payment already verified.",
                        "booking_status": booking.status,
                    })
                return Response(
                    {"error": "This payment has already been processed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if payment.status != Payment.Status.PENDING:
                return Response(
                    {"error": "This payment is not pending."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking.status != "PENDING":
                return Response(
                    {"error": "This booking cannot be confirmed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                not booking.hold_expires_at
                or booking.hold_expires_at <= timezone.now()
            ):
                return Response(
                    {"error": "The booking hold has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
                f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(
                expected_signature,
                razorpay_signature,
            ):
                return Response(
                    {"error": "Payment signature verification failed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Signature verification alone does not establish the
            # captured payment status. Verify with Razorpay before
            # marking the booking as confirmed.
            client = get_razorpay_client()
            gateway_payment = client.payment.fetch(razorpay_payment_id)

            if gateway_payment.get("order_id") != razorpay_order_id:
                return Response(
                    {"error": "Payment does not match this order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if gateway_payment.get("status") != "captured":
                return Response(
                    {"error": "Payment has not been captured yet."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            expected_amount = int(
                (Decimal(str(payment.amount)) * 100)
                .quantize(Decimal("1"))
            )

            if int(gateway_payment.get("amount", 0)) != expected_amount:
                return Response(
                    {"error": "The payment amount does not match the booking."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if gateway_payment.get("currency") != payment.currency:
                return Response(
                    {"error": "The payment currency does not match."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = Payment.Status.SUCCESS
            payment.save()

            booking.status = "CONFIRMED"
            booking.save(update_fields=["status"])

            return Response({
                "message": "Payment verified successfully.",
                "booking_status": booking.status,
            })

    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Booking.DoesNotExist:
        return Response(
            {"error": "Booking not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except razorpay.errors.RazorpayError:
        return Response(
            {"error": "Could not verify payment with Razorpay. Please retry."},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def download_booking_pdf(request, booking_id):
    payment = (
        Payment.objects
        .filter(
            booking_id=booking_id,
            status=Payment.Status.SUCCESS,
            booking__status=Booking.Status.CONFIRMED,
        )
        .select_related("booking", "booking__availability")
        .order_by("-created_at")
        .first()
    )

    if payment is None:
        return Response(
            {"error": "No successful payment found for this booking."},
            status=status.HTTP_404_NOT_FOUND,
        )

    booking = payment.booking

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="booking_{booking.id}_confirmation.pdf"'
    )

    pdf = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        "BrandTitle",
        parent=styles["Title"],
        fontSize=21,
        leading=26,
        textColor=colors.HexColor("#9f1239"),
        spaceAfter=5,
        alignment=1,
    )

    subtitle_style = ParagraphStyle(
        "ConfirmationSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#555555"),
        alignment=1,
        spaceAfter=8,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#9f1239"),
        spaceBefore=12,
        spaceAfter=8,
    )

    story = []

    # PDF heading
    story.append(Paragraph("RENT A COMPANION", brand_style))
    story.append(
        Paragraph("BOOKING &amp; STYLE CONFIRMATION", subtitle_style)
    )
    story.append(
        Paragraph(
            f"Booking Reference #{booking.id}",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 15))

    # Booking and payment details
    story.append(Paragraph("01. BOOKING DETAILS", section_style))

    details = [
        ["Customer name", str(booking.customer_name)],
        ["Phone number", str(booking.customer_phone)],
        ["District", str(booking.district)],
        [
            "Booking date",
            booking.availability.date.strftime("%d %B %Y"),
        ],
        [
            "Start time",
            booking.start_time.strftime("%I:%M %p")
            if booking.start_time else "Not specified",
        ],
        [
            "End time",
            booking.end_time.strftime("%I:%M %p")
            if booking.end_time else "Not specified",
        ],
        ["Duration", f"{booking.booked_hours} hours"],
        [
            "Activities",
            ", ".join(
                booking.activities.values_list("name", flat=True)
            ) or "None selected",
        ],
    ]

    details_table = Table(
        details,
        colWidths=[145, 345],
        repeatRows=0,
    )

    details_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8e9ee")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5d5da")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(details_table)
    story.append(Spacer(1, 12))

    # Selected outfits and their actual catalogue images
    story.append(Paragraph("02. SELECTED OUTFITS", section_style))

    selections = (
        booking.outfit_selections
        .select_related("outfit_item", "outfit_item__category")
        .all()
    )

    if not selections.exists():
        story.append(
            Paragraph(
                "No outfits were selected for this booking.",
                styles["Normal"],
            )
        )
    else:
        current_category = None

        for selection in selections:
            item = selection.outfit_item
            category_name = item.category.name

            if category_name != current_category:
                current_category = category_name
                story.append(
                    Paragraph(
                        category_name,
                        styles["Heading3"],
                    )
                )

            # Prefer the original catalogue image on local storage.
            outfit_image = None

            try:
                if item.image and item.image.name:
                    image_path = item.image.path

                    if os.path.isfile(image_path):
                        outfit_image = Image(
                            image_path,
                            width=90,
                            height=90,
                            kind="proportional",
                        )
            except (AttributeError, NotImplementedError, ValueError, OSError):
                # Some cloud storage backends do not provide a local path.
                outfit_image = None

            if outfit_image is None:
                image_content = Paragraph(
                    "Image unavailable",
                    styles["Italic"],
                )
            else:
                image_content = outfit_image

            outfit_name = Paragraph(
                str(selection.item_name),
                styles["Heading4"],
            )

            specifications = (
                selection.item_specifications
                or "No additional specifications"
            )

            outfit_description = Paragraph(
                str(specifications).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"),
                styles["Normal"],
            )

            outfit_table = Table(
                [[
                    image_content,
                    [outfit_name, Spacer(1, 5), outfit_description],
                ]],
                colWidths=[110, 380],
            )

            outfit_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf7f8")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5d5da")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))

            story.append(outfit_table)
            story.append(Spacer(1, 8))

    # Verified payment details
    story.append(Paragraph("03. PAYMENT CONFIRMATION", section_style))

    payment_details = [
        ["Amount paid", f"INR {payment.amount}"],
        ["Payment status", "SUCCESS"],
        [
            "Razorpay payment reference",
            payment.razorpay_payment_id or "Not available",
        ],
    ]

    payment_table = Table(
        payment_details,
        colWidths=[200, 290],
    )

    payment_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8e9ee")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5d5da")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(payment_table)
    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "This document confirms that payment was verified successfully.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Thank you for choosing Rent a Companion.",
            subtitle_style,
        )
    )

    pdf.build(story)
    return response
