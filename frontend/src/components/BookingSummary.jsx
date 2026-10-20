
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./BookingSummary.css";

const WHATSAPP_NUMBER = "919061735003";

const PAYMENT_API_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const PAYMENT_API_BASE = `${PAYMENT_API_URL.replace(/\/+$/, "")}/api`;

function BookingSummary() {
  const { state } = useLocation();

  const [paying, setPaying] = useState(false);
  const [message, setMessage] = useState("");
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  if (!state?.booking) {
    return (
      <div className="booking-page">
        <div className="booking-container">
          <h1>No booking found</h1>
          <p>Please create a booking first.</p>

          <Link to="/booking" className="summary-button">
            Go to Booking
          </Link>
        </div>
      </div>
    );
  }

  const {
    booking,
    customerName,
    district,
    selectedDate,
    startTime,
    bookedHours,
  } = state;

  async function handlePayment() {
    if (paying || paymentSuccess) return;

    setPaying(true);
    setMessage("");

    try {
      if (!window.Razorpay) {
        throw new Error(
          "Razorpay checkout did not load. Please refresh and try again."
        );
      }

      // Step 1: Ask Django to create a payment order.
      const orderResponse = await fetch(
        `${PAYMENT_API_BASE}/create-order/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            booking_id: booking.id,
          }),
        }
      );

      const orderData = await orderResponse.json();

      if (!orderResponse.ok) {
        throw new Error(
          orderData.error || "Could not create the payment order."
        );
      }

      // Step 2: Open Razorpay checkout.
      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "Rent a Companion",
        description: `Booking #${booking.id}`,
        order_id: orderData.order_id,

        handler: async function (response) {
          try {
            setMessage(
              "Payment received. Verifying with the server..."
            );

            // Step 3: Ask Django to verify the payment.
            const verifyResponse = await fetch(
              `${PAYMENT_API_BASE}/verify-payment/`,
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  booking_id: booking.id,
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                }),
              }
            );

            const verifyData = await verifyResponse.json();

            if (!verifyResponse.ok) {
              throw new Error(
                verifyData.error || "Payment verification failed."
              );
            }

            setPaymentSuccess(true);
            setMessage(
              "Payment verified! Your booking is confirmed."
            );
          } catch (error) {
            setMessage(
              `${error.message} Do not pay again immediately. Check the payment status first.`
            );
          } finally {
            setPaying(false);
          }
        },

        modal: {
          ondismiss: function () {
            setPaying(false);
            setMessage(
              "Checkout closed. Your booking is not confirmed yet."
            );
          },
        },

        theme: {
          color: "#9f1239",
        },
      };

      const checkout = new window.Razorpay(options);

      checkout.on("payment.failed", function (response) {
        setPaying(false);
        setMessage(
          response.error?.description ||
            "Payment failed. Please try again."
        );
      });

      checkout.open();
    } catch (error) {
      setPaying(false);
      setMessage(error.message || "Something went wrong.");
    }
  }

  return (
    <div className="booking-page">
      <div className="booking-container">
        <h1>Review Your Booking</h1>

        <p className="booking-description">
          Check your details before continuing to payment.
        </p>

        <div className="summary-details">
          <p>
            <strong>Name:</strong> {customerName}
          </p>

          <p>
            <strong>Booking ID:</strong> {booking.id}
          </p>

          <p>
            <strong>Date:</strong> {selectedDate}
          </p>

          <p>
            <strong>District:</strong> {district}
          </p>

          <p>
            <strong>Start time:</strong> {startTime}
          </p>

          <p>
            <strong>Duration:</strong> {bookedHours} hours
          </p>

          <p>
            <strong>Status:</strong>{" "}
            {paymentSuccess ? "CONFIRMED" : booking.status}
          </p>

          <h2>Total: ₹{booking.total_amount}</h2>
        </div>

        {message && (
          <p role="status" aria-live="polite">
            {message}
          </p>
        )}

        {!paymentSuccess && (
          <button
            type="button"
            className="booking-submit"
            onClick={handlePayment}
            disabled={paying}
          >
            {paying ? "Processing..." : "Continue to Payment"}
          </button>
        )}

        {paymentSuccess && (
          <>
            <a
              href={`${PAYMENT_API_BASE}/booking-pdf/${booking.id}/`}
              className="booking-submit"
              target="_blank"
              rel="noopener noreferrer"
              download
            >
              Download Booking PDF
            </a>

            <button
              type="button"
              className="booking-submit whatsapp-button"
              onClick={() => {
                const whatsappMessage = encodeURIComponent(
                  `Hi, I've completed my booking with Rent a Companion.
Booking ID: ${booking.id}
Name: ${customerName}
District: ${district}
Date: ${selectedDate}
Start time: ${startTime}
Duration: ${bookedHours} hours

I'd like to coordinate my booking details.`
                );

                window.open(
                  `https://wa.me/${WHATSAPP_NUMBER}?text=${whatsappMessage}`,
                  "_blank",
                  "noopener,noreferrer"
                );
              }}
            >
              Message me on WhatsApp
            </button>
          </>
        )}

        <p>
          <Link to="/booking">Back to booking form</Link>
        </p>
      </div>
    </div>
  );
}

export default BookingSummary;
