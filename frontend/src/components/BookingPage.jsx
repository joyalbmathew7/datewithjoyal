import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./BookingPage.css";
import OutfitSelector from "./OutfitSelector";
const API_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const BOOKING_API_BASE = `${API_URL.replace(/\/+$/, "")}/api/v1`;
// const BOOKING_API_BASE = `${API_URL.replace(/\/+$/, "")}/api/v1`;ITE_API_BASE_URL;

function getMinutes(time) {
  const [hours, minutes] = time.slice(0, 5).split(":").map(Number);
  return hours * 60 + minutes;
}

function BookingPage() {
  const [selectedOutfits, setSelectedOutfits] = useState([]);
  const [slots, setSlots] = useState([]);
  const [selectedSlotId, setSelectedSlotId] = useState("");
  const [district, setDistrict] = useState("");
  const [startTime, setStartTime] = useState("");
  const [bookedHours, setBookedHours] = useState("4");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAge, setCustomerAge] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    async function loadAvailability() {
      try {
        const response = await fetch(
  `${BOOKING_API_BASE}/availability/`
);

        if (!response.ok) {
          throw new Error("Could not load available dates.");
        }

        const data = await response.json();
        setSlots(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadAvailability();
  }, []);

  const selectedSlot = slots.find(
    (slot) => String(slot.id) === selectedSlotId
  );

  const bookedPeriods = selectedSlot?.booked_periods || [];

  const availableStartTimes = selectedSlot
    ? Array.from(
        {
          length: Math.floor(
            (getMinutes(selectedSlot.end_time) -
              getMinutes(selectedSlot.start_time)) / 30
          ),
        },
        (_, index) => getMinutes(selectedSlot.start_time) + index * 30
      ).filter((start) => {
        const windowEnd = getMinutes(selectedSlot.end_time);

        if (start + 4 * 60 > windowEnd) return false;

        return !bookedPeriods.some((period) => {
          const bookedStart = getMinutes(period.start_time);
          const bookedEnd = getMinutes(period.end_time);

          return start < bookedEnd && start + 4 * 60 > bookedStart;
        });
      })
    : [];

  const availableDurations =
    selectedSlot && startTime
      ? [4, 5, 6, 7, 8].filter((hours) => {
          const requestedStart = getMinutes(startTime);
          const requestedEnd = requestedStart + hours * 60;

          if (requestedEnd > getMinutes(selectedSlot.end_time)) {
            return false;
          }

          return !bookedPeriods.some((period) => {
            const bookedStart = getMinutes(period.start_time);
            const bookedEnd = getMinutes(period.end_time);

            return requestedStart < bookedEnd && requestedEnd > bookedStart;
          });
        })
      : [];

  function handleSlotChange(event) {
    setSelectedSlotId(event.target.value);
    setDistrict("");
    setStartTime("");
  }

  function handleStartTimeChange(event) {
    setStartTime(event.target.value);
    setBookedHours("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setSubmitting(true);
    setSubmitError("");

    try {
    const response = await fetch(`${BOOKING_API_BASE}/bookings/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        customer_name: customerName,
        customer_phone: customerPhone,
        customer_age: Number(customerAge),
        district: district,
        availability: Number(selectedSlotId),
        start_time: startTime,
        booked_hours: Number(bookedHours),
        activity_ids: [],
        outfit_item_ids: selectedOutfits.map((item) => item.item_id),
      }),
    });

      const data = await response.json();

      if (!response.ok) {
        const message =
          typeof data === "object"
            ? Object.entries(data)
                .map(([field, errors]) => {
                  const details = Array.isArray(errors)
                    ? errors.join(", ")
                    : typeof errors === "object"
                      ? JSON.stringify(errors)
                      : String(errors);

                  return `${field}: ${details}`;
                })
                .join("\n")
            : "Booking failed.";

        throw new Error(message);
      }

      navigate("/booking-summary", {
        state: {
          booking: data,
          customerName,
          district,
          selectedDate: selectedSlot.date,
          startTime: startTime.slice(0, 5),
          bookedHours,
        },
      });
    } catch (err) {
      setSubmitError(
        err.message || "Could not create booking. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="booking-page">
      <div className="booking-container">
        <h1>Book Your Experience</h1>
        <p className="booking-description">
          Choose an available date, location, and time.
        </p>

        {loading && (
          <p className="booking-status" role="status">
            Loading available dates...
          </p>
        )}

        {error && (
          <p className="booking-error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && slots.length === 0 && (
          <p className="booking-status">No available dates right now.</p>
        )}

        {!loading && !error && slots.length > 0 && (
          <form className="booking-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="availability">Available date</label>
              <select
                id="availability"
                value={selectedSlotId}
                onChange={handleSlotChange}
                required
              >
                <option value="">Choose a date</option>

                {slots.map((slot) => (
                  <option key={slot.id} value={slot.id}>
                    {slot.date} ({slot.start_time.slice(0, 5)} -{" "}
                    {slot.end_time.slice(0, 5)})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="district">Available district</label>
              <select
                id="district"
                value={district}
                onChange={(event) => setDistrict(event.target.value)}
                disabled={!selectedSlot}
                required
              >
                <option value="">Choose a district</option>

                {selectedSlot?.districts.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="startTime">Start time</label>
              <select
                id="startTime"
                value={startTime}
                onChange={handleStartTimeChange}
                disabled={!selectedSlot || !district}
                required
              >
                <option value="">Choose a start time</option>

                {availableStartTimes.map((minutes) => {
                  const hours = String(Math.floor(minutes / 60)).padStart(
                    2,
                    "0"
                  );
                  const mins = String(minutes % 60).padStart(2, "0");
                  const value = `${hours}:${mins}:00`;

                  return (
                    <option key={value} value={value}>
                      {hours}:{mins}
                    </option>
                  );
                })}
              </select>

              {selectedSlot && district && availableStartTimes.length === 0 && (
                <p className="form-hint">
                  No start times are available for this date.
                </p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="duration">Duration</label>
              <select
                id="duration"
                value={bookedHours}
                onChange={(event) => setBookedHours(event.target.value)}
                disabled={!startTime}
                required
              >
                <option value="">Choose duration</option>

                {availableDurations.map((hours) => (
                  <option key={hours} value={hours}>
                    {hours} hours
                  </option>
                ))}
              </select>

              {startTime && availableDurations.length === 0 && (
                <p className="form-hint">No durations fit this start time.</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="customerName">Your name</label>
              <input
                id="customerName"
                value={customerName}
                onChange={(event) => setCustomerName(event.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="customerPhone">Phone number</label>
              <input
                id="customerPhone"
                type="tel"
                value={customerPhone}
                onChange={(event) => setCustomerPhone(event.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="customerAge">Age</label>
              <input
                id="customerAge"
                type="number"
                min="18"
                value={customerAge}
                onChange={(event) => setCustomerAge(event.target.value)}
                required
              />
            </div>

            <OutfitSelector onSelectionChange={setSelectedOutfits} />

            <button
              type="submit"
              className="booking-submit"
              disabled={submitting}
            >
              {submitting ? "Creating booking..." : "Continue to Booking"}
            </button>
          </form>
        )}

        {submitError && (
          <p className="booking-error" role="alert">
            {submitError}
          </p>
        )}
      </div>
    </div>
  );
}

export default BookingPage;