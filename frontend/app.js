
// ============================================
// CHITRAL TOURISM EXPLORER
// Frontend JavaScript
// ============================================

const API_BASE = "http://127.0.0.1:8001/api";

let map;
let allLocations = [];
let markers = [];
let markerLayer;

// DOM elements
const mapElement = document.getElementById("map");
const placesList = document.getElementById("places-list");
const searchInput = document.getElementById("search-input");
const categoryFilter = document.getElementById("category-filter");
const resultCount = document.getElementById("result-count");
const resetButton = document.getElementById("reset-view");
const detailCard = document.getElementById("detail-card");

// ============================================
// INITIALIZE APPLICATION
// ============================================

document.addEventListener("DOMContentLoaded", async () => {
    if (!mapElement) {
        console.error("Map element with id='map' was not found.");
        return;
    }

    initializeMap();
    attachEventListeners();

    await loadLocations();
});

// ============================================
// INITIALIZE LEAFLET MAP
// ============================================

function initializeMap() {
    map = L.map("map").setView([36.0, 72.0], 8);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    markerLayer = L.layerGroup().addTo(map);

    setTimeout(() => {
        map.invalidateSize();
    }, 500);
}

// ============================================
// LOAD LOCATIONS FROM FASTAPI
// ============================================

async function loadLocations() {
    try {
        if (placesList) {
            placesList.innerHTML = "<p>Loading tourist locations...</p>";
        }

        const response = await fetch(`${API_BASE}/locations`);

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();

        allLocations = Array.isArray(data.locations)
            ? data.locations
            : [];

        allLocations = allLocations.filter(location =>
            Number.isFinite(Number(location.latitude)) &&
            Number.isFinite(Number(location.longitude))
        );

        updateStatistics();
        populateCategories();
        displayLocations(allLocations);

        console.log("Locations loaded successfully:", allLocations.length);

    } catch (error) {
        console.error("Error loading locations:", error);

        if (placesList) {
            placesList.innerHTML =
                "<p>Unable to load tourist locations. Check that the backend server is running on port 8001.</p>";
        }

        if (resultCount) {
            resultCount.textContent = "0 locations";
        }
    }
}

// ============================================
// UPDATE DASHBOARD STATISTICS
// ============================================

function updateStatistics() {
    const uniqueCategories = new Set(
        allLocations.map(location => location.category)
    );

    const locationStat = document.getElementById("stat-locations");
    const categoryStat = document.getElementById("stat-categories");

    if (locationStat) {
        locationStat.textContent = allLocations.length;
    }

    if (categoryStat) {
        categoryStat.textContent = uniqueCategories.size;
    }
}

// ============================================
// POPULATE CATEGORY FILTER
// ============================================

function populateCategories() {
    if (!categoryFilter) return;

    const selectedValue = categoryFilter.value;

    const categories = [
        ...new Set(
            allLocations
                .map(location => location.category)
                .filter(Boolean)
        )
    ].sort();

    categoryFilter.innerHTML = '<option value="">All Categories</option>';

    categories.forEach(category => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
    });

    if (categories.includes(selectedValue)) {
        categoryFilter.value = selectedValue;
    }
}

// ============================================
// DISPLAY LOCATIONS
// ============================================

function displayLocations(locations) {
    markerLayer.clearLayers();
    markers = [];

    displayPlacesList(locations);
    displayMapMarkers(locations);

    if (resultCount) {
        resultCount.textContent =
            `${locations.length} locations found`;
    }
}

// ============================================
// DISPLAY LOCATION LIST
// ============================================

function displayPlacesList(locations) {
    if (!placesList) return;

    placesList.innerHTML = "";

    if (locations.length === 0) {
        placesList.innerHTML = "<p>No tourist locations found.</p>";
        return;
    }

    locations.forEach(location => {
        const item = document.createElement("div");

        item.className = "place-item";
        item.dataset.id = location.id;

        item.innerHTML = `
            <h3>${escapeHTML(location.name)}</h3>
            <p>${escapeHTML(location.category || "Tourist Location")}</p>
            <small>${escapeHTML(location.description || "")}</small>
        `;

        item.addEventListener("click", () => {
            showLocationDetails(location.id);
        });

        placesList.appendChild(item);
    });
}

// ============================================
// DISPLAY MAP MARKERS
// ============================================

function displayMapMarkers(locations) {

    // Group locations that have identical coordinates.
    // This prevents markers from hiding one another.

    const coordinateGroups = new Map();

    locations.forEach(location => {
        const latitude = Number(location.latitude);
        const longitude = Number(location.longitude);

        const key = `${latitude.toFixed(5)},${longitude.toFixed(5)}`;

        if (!coordinateGroups.has(key)) {
            coordinateGroups.set(key, []);
        }

        coordinateGroups.get(key).push(location);
    });

    coordinateGroups.forEach(group => {

        const firstLocation = group[0];

        const marker = L.marker([
            Number(firstLocation.latitude),
            Number(firstLocation.longitude)
        ]);

        const popupContent = `
            <div class="map-popup">
                <strong>${group.length > 1
                ? `${group.length} locations`
                : escapeHTML(firstLocation.name)
            }</strong>

                ${group.map(location => `
                    <div class="popup-location">
                        <p>
                            <strong>${escapeHTML(location.name)}</strong>
                        </p>

                        <small>${escapeHTML(location.category || "")}</small>

                        <br>

                        <button
                            type="button"
                            class="popup-detail-button"
                            data-location-id="${location.id}">
                            View Details
                        </button>
                    </div>
                `).join("")}
            </div>
        `;

        marker.bindPopup(popupContent);

        marker.addTo(markerLayer);
        markers.push(marker);
    });

    // Zoom to all visible locations.
    if (markers.length > 0) {
        const markerBounds = L.featureGroup(markers).getBounds();

        if (markerBounds.isValid()) {
            map.fitBounds(markerBounds, {
                padding: [35, 35],
                maxZoom: 10
            });
        }
    }
}

// ============================================
// SHOW LOCATION DETAILS
// ============================================

function showLocationDetails(locationId) {
    const location = allLocations.find(
        item => Number(item.id) === Number(locationId)
    );

    if (!location) return;

    if (detailCard) {
        detailCard.innerHTML = `
            <div class="location-details">

                <h2>${escapeHTML(location.name)}</h2>

                <p>
                    <strong>Category:</strong>
                    ${escapeHTML(location.category || "Not available")}
                </p>

                <p>
                    <strong>Description:</strong>
                    ${escapeHTML(location.description || "No description available")}
                </p>

                <p>
                    <strong>Accessibility:</strong>
                    ${escapeHTML(location.accessibility || "Not available")}
                </p>

                <p>
                    <strong>Best Visit Season:</strong>
                    ${escapeHTML(location.best_visit_season || "Not available")}
                </p>

                <p>
                    <strong>Latitude:</strong>
                    ${Number(location.latitude).toFixed(5)}
                </p>

                <p>
                    <strong>Longitude:</strong>
                    ${Number(location.longitude).toFixed(5)}
                </p>

                <button
                    type="button"
                    id="close-details">
                    Close Details
                </button>

            </div>
        `;

        detailCard.style.display = "block";

        const closeButton = document.getElementById("close-details");

        if (closeButton) {
            closeButton.addEventListener("click", () => {
                detailCard.style.display = "none";
            });
        }
    }

    // Move map to selected location.
    map.setView([
        Number(location.latitude),
        Number(location.longitude)
    ], 12);

    // Open the marker popup containing this location.
    markers.forEach(marker => {
        const position = marker.getLatLng();

        if (
            Math.abs(position.lat - Number(location.latitude)) < 0.00001 &&
            Math.abs(position.lng - Number(location.longitude)) < 0.00001
        ) {
            marker.openPopup();
        }
    });
}

// ============================================
// SEARCH AND CATEGORY FILTER
// ============================================

function filterLocations() {
    const searchTerm = searchInput
        ? searchInput.value.toLowerCase().trim()
        : "";

    const selectedCategory = categoryFilter
        ? categoryFilter.value
        : "";

    const filteredLocations = allLocations.filter(location => {

        const matchesSearch =
            (location.name || "").toLowerCase().includes(searchTerm) ||
            (location.category || "").toLowerCase().includes(searchTerm) ||
            (location.description || "").toLowerCase().includes(searchTerm);

        const matchesCategory =
            !selectedCategory ||
            location.category === selectedCategory;

        return matchesSearch && matchesCategory;
    });

    displayLocations(filteredLocations);
}

// ============================================
// RESET MAP AND FILTERS
// ============================================

function resetView() {
    if (searchInput) {
        searchInput.value = "";
    }

    if (categoryFilter) {
        categoryFilter.value = "";
    }

    if (detailCard) {
        detailCard.style.display = "none";
    }

    displayLocations(allLocations);
}

// ============================================
// EVENT LISTENERS
// ============================================

function attachEventListeners() {

    if (searchInput) {
        searchInput.addEventListener("input", filterLocations);
    }

    if (categoryFilter) {
        categoryFilter.addEventListener("change", filterLocations);
    }

    if (resetButton) {
        resetButton.addEventListener("click", resetView);
    }

    // Handle buttons inside Leaflet popups.
    document.addEventListener("click", event => {

        const button = event.target.closest(".popup-detail-button");

        if (button) {
            const locationId = button.dataset.locationId;
            showLocationDetails(locationId);
        }
    });

    // Mobile navigation.
    const menuToggle = document.getElementById("menu-toggle");
    const mainNav = document.getElementById("main-nav");

    if (menuToggle && mainNav) {
        menuToggle.addEventListener("click", () => {
            mainNav.classList.toggle("active");
        });
    }
}

// ============================================
// SAFE HTML TEXT
// ============================================

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}
