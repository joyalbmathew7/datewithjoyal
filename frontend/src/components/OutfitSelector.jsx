import { useEffect, useRef, useState } from "react";
import "./OutfitSelector.css";

const API_URL = import.meta.env.VITE_API_BASE_URL;

function OutfitSelector({ onSelectionChange }) {
  const [categories, setCategories] = useState([]);
  const [selectedItems, setSelectedItems] = useState({});
  const [skipped, setSkipped] = useState({});
  const [activeIndex, setActiveIndex] = useState(0);
  const [finished, setFinished] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [edges, setEdges] = useState({ start: true, end: true });

  const trackRef = useRef(null);

  useEffect(() => {
    async function loadOutfits() {
      try {
        const response = await fetch(`${API_URL}/outfits/`);

        if (!response.ok) {
          throw new Error("Could not load clothing options.");
        }

        const data = await response.json();
        setCategories(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadOutfits();
  }, []);

  function updateEdges() {
    const el = trackRef.current;
    if (!el) return;

    setEdges({
      start: el.scrollLeft <= 4,
      end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4,
    });
  }

  // Reset the carousel to the first card whenever the category changes.
  useEffect(() => {
    if (trackRef.current) {
      trackRef.current.scrollLeft = 0;
    }
    updateEdges();
  }, [activeIndex, categories, finished]);

  useEffect(() => {
    window.addEventListener("resize", updateEdges);
    return () => window.removeEventListener("resize", updateEdges);
  }, []);

  function handleSelect(categoryId, itemId) {
    const updated = {
      ...selectedItems,
      [categoryId]: selectedItems[categoryId] === itemId ? null : itemId,
    };

    setSelectedItems(updated);

    if (updated[categoryId] !== null) {
      setSkipped((prev) => ({ ...prev, [categoryId]: false }));
    }

    const selections = Object.entries(updated)
      .filter(([, selectedId]) => selectedId !== null)
      .map(([selectedCategoryId, selectedId]) => ({
        category_id: Number(selectedCategoryId),
        item_id: selectedId,
      }));

    onSelectionChange?.(selections);
  }

  function scrollCards(direction) {
    const el = trackRef.current;
    if (!el) return;

    el.scrollBy({ left: direction * el.clientWidth * 0.8, behavior: "smooth" });
  }

  function goToStep(index) {
    setFinished(false);
    setActiveIndex(index);
  }

  if (loading) {
    return <p className="outfit-status">Loading clothing options...</p>;
  }

  if (error) {
    return (
      <p className="outfit-error" role="alert">
        {error}
      </p>
    );
  }

  if (categories.length === 0) {
    return null;
  }

  const category = categories[activeIndex];
  const selectedId = selectedItems[category.id] ?? null;
  const isLast = activeIndex === categories.length - 1;
  const nextCategory = categories[activeIndex + 1];

  function handlePrimary() {
    if (selectedId === null) {
      setSkipped((prev) => ({ ...prev, [category.id]: true }));
    }

    if (isLast) {
      setFinished(true);
    } else {
      setActiveIndex(activeIndex + 1);
    }
  }

  function findSelectedItem(cat) {
    const id = selectedItems[cat.id];
    return id == null ? null : cat.items.find((item) => item.id === id);
  }

  function stepStatus(cat) {
    const item = findSelectedItem(cat);
    if (item) return item.name;
    if (skipped[cat.id]) return "Skipped";
    return "Not chosen";
  }

  return (
    <section className="outfit-selector">
      <h2>Choose Your Outfit</h2>
      <p className="outfit-description">
        Pick one item per category, or skip any you don't need.
      </p>

      {/* Step tabs */}
      <ol className="outfit-steps">
        {categories.map((cat, index) => {
          const chosen = findSelectedItem(cat);
          const isActive = !finished && index === activeIndex;

          return (
            <li key={cat.id}>
              <button
                type="button"
                className={`outfit-step ${isActive ? "active" : ""} ${
                  chosen ? "done" : ""
                }`}
                onClick={() => goToStep(index)}
                aria-current={isActive ? "step" : undefined}
              >
                <span className="outfit-step-mark" aria-hidden="true">
                  {chosen ? "✓" : index + 1}
                </span>
                <span className="outfit-step-text">
                  <span className="outfit-step-name">{cat.name}</span>
                  <span className="outfit-step-status">{stepStatus(cat)}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      {finished ? (
        <div className="outfit-summary">
          <h3>Your outfit</h3>

          <ul className="outfit-summary-list">
            {categories.map((cat) => {
              const item = findSelectedItem(cat);

              return (
                <li key={cat.id} className="outfit-summary-item">
                  {item ? (
                    <img src={item.image} alt="" />
                  ) : (
                    <span className="outfit-summary-empty" aria-hidden="true">
                      –
                    </span>
                  )}
                  <span>
                    <strong>{cat.name}</strong>
                    <br />
                    {item ? item.name : "Skipped"}
                  </span>
                </li>
              );
            })}
          </ul>

          <button
            type="button"
            className="outfit-link-button"
            onClick={() => goToStep(0)}
          >
            Change outfit
          </button>
        </div>
      ) : (
        <div className="outfit-category">
          <h3>{category.name}</h3>

          {category.items.length === 0 ? (
            <p className="outfit-empty">
              No items available in this category yet.
            </p>
          ) : (
            <div className="outfit-carousel">
              <button
                type="button"
                className="outfit-arrow outfit-arrow-prev"
                onClick={() => scrollCards(-1)}
                disabled={edges.start}
                aria-label={`Previous ${category.name} items`}
              >
                ‹
              </button>

              <div
                className="outfit-track"
                ref={trackRef}
                onScroll={updateEdges}
                key={category.id}
              >
                {category.items.map((item) => {
                  const selected = selectedId === item.id;

                  return (
                    <button
                      type="button"
                      key={item.id}
                      className={`outfit-card ${selected ? "selected" : ""}`}
                      onClick={() => handleSelect(category.id, item.id)}
                      aria-pressed={selected}
                    >
                      <span className="outfit-image-wrap">
                        <img
                          src={item.image}
                          alt={item.name}
                          className="outfit-image"
                          loading="lazy"
                        />
                        {selected && (
                          <span className="outfit-selected">Selected ✓</span>
                        )}
                      </span>

                      <span className="outfit-item-name">{item.name}</span>

                      {item.specifications && (
                        <span className="outfit-specifications">
                          {item.specifications}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              <button
                type="button"
                className="outfit-arrow outfit-arrow-next"
                onClick={() => scrollCards(1)}
                disabled={edges.end}
                aria-label={`Next ${category.name} items`}
              >
                ›
              </button>
            </div>
          )}

          <div className="outfit-actions">
            <button
              type="button"
              className="outfit-link-button"
              onClick={() => setActiveIndex(activeIndex - 1)}
              disabled={activeIndex === 0}
            >
              ‹ Back
            </button>

            {selectedId !== null && (
              <button
                type="button"
                className="outfit-link-button"
                onClick={() => handleSelect(category.id, null)}
              >
                Remove {category.name}
              </button>
            )}

            <button
              type="button"
              className={`outfit-primary ${
                selectedId === null ? "is-skip" : ""
              }`}
              onClick={handlePrimary}
            >
              {selectedId === null
                ? `No Suggestion for  ${category.name}`
                : isLast
                  ? "Finish outfit"
                  : `Next: ${nextCategory.name}`}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export default OutfitSelector;