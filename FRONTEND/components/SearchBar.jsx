import { useState } from "react";

export default function SearchBar({
                                      onSearch,
                                      onCurrentLocation,
                                  }) {

    const [location, setLocation] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");

    const handleSubmit = (e) => {

        e.preventDefault();

        if (!location.trim()) return;

        onSearch(location, startDate, endDate);

    };

    return (

        <form
            onSubmit={handleSubmit}
            className="bg-white rounded-xl shadow-lg p-6 mb-8"
        >

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                <input
                    type="text"
                    placeholder="City, ZIP, Landmark..."
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="border rounded-lg p-3"
                    required
                />

                <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="border rounded-lg p-3"
                />

                <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="border rounded-lg p-3"
                />

            </div>

            <p className="text-sm text-gray-500 mt-3">
                Leave the dates blank to view the default 5-day forecast.
            </p>

            <div className="flex flex-col md:flex-row gap-4 mt-5">

                <button
                    type="submit"
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
                >
                    Search Weather
                </button>

                <button
                    type="button"
                    onClick={onCurrentLocation}
                    className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700"
                >
                    📍 Use My Current Location
                </button>

            </div>

        </form>

    );

}
