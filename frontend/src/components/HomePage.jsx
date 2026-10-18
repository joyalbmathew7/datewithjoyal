import "./HomePage.css";
import Navbar from "./Navbar";
import { Link } from "react-router-dom";

function HomePage() {
  return (
    <div className="home-page">
      <Navbar />

      <section className="hero">
        <p className="hero-label">Your time, your experience</p>

        <h1>
          Good Company.
          <br />
          Memorable Moments.
        </h1>

        <p className="hero-description">
          Book a companion for a movie, shopping, a meal, or a day exploring
          your favourite places.
        </p>

        <Link to="/booking" className="hero-button">
          Explore Booking
        </Link>
      </section>

      <section className="experiences">
        <h2>Choose Your Experience</h2>

        <div className="experience-list">
          <article className="experience-card">
            <span className="experience-icon" aria-hidden="true">🎬</span>
            <h3>Movie</h3>
            <p>Enjoy a movie together.</p>
          </article>

          <article className="experience-card">
            <span className="experience-icon" aria-hidden="true">🛍️</span>
            <h3>Shopping</h3>
            <p>Make shopping more enjoyable.</p>
          </article>

          <article className="experience-card">
            <span className="experience-icon" aria-hidden="true">☕</span>
            <h3>Meal or Coffee</h3>
            <p>Share a relaxed conversation.</p>
          </article>
        </div>
      </section>

      <section id="booking" className="booking-intro">
        <h2>Ready to Book?</h2>
        <p>Choose your date, time, and preferred location.</p>

        <Link to="/booking" className="hero-button">
          Start Booking
        </Link>
      </section>

      <footer className="home-footer">© 2026 Rent a Companion</footer>
    </div>
  );
}

export default HomePage;