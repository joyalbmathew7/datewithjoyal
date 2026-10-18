import "./Navbar.css";
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <header className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="navbar-heart" aria-hidden="true">♡</span>
        Rent a Companion
      </Link>

      <Link to="/booking" className="navbar-button">
        Book Now
      </Link>
    </header>
  );
}

export default Navbar;