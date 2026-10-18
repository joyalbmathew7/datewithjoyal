
import { BrowserRouter, Routes, Route } from "react-router-dom";

import HomePage from "./components/HomePage";
import BookingPage from "./components/BookingPage";
import BookingSummary from "./components/BookingSummary";
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/booking" element={<BookingPage />} />
              <Route
        path="/booking-summary"
        element={<BookingSummary />}
      />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
