import { useState } from "react";

export default function UpdateRecord({ record, onUpdate, onCancel }) {

    const [location, setLocation] = useState(record.location_query);
    const [startDate, setStartDate] = useState(record.start_date);
    const [endDate, setEndDate] = useState(record.end_date);

    const [loading, setLoading] = useState(false);

    const handleUpdate = async () => {

        setLoading(true);

        await onUpdate(record.id, {
            location_query: location,
            start_date: startDate,
            end_date: endDate,
        });

        setLoading(false);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 mt-10">

            <h2 className="text-2xl font-bold mb-6">
                Update Weather Record
            </h2>

            <div className="space-y-4">

                <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full border rounded-lg p-3"
                />

                <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full border rounded-lg p-3"
                />

                <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full border rounded-lg p-3"
                />

                <div className="flex flex-col md:flex-row gap-4">

                    <button
                        onClick={handleUpdate}
                        disabled={loading}
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg"
                    >
                        {loading ? "Updating..." : "Update Record"}
                    </button>

                    <button
                        onClick={onCancel}
                        className="bg-gray-500 text-white px-6 py-3 rounded-lg"
                    >
                        Cancel
                    </button>

                </div>

            </div>

        </div>
    );
}
