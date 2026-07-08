import { useState } from "react";
import { createRecord } from "../api/client";

export default function RecordForm({
                                     searchedLocation,
                                     searchedStartDate,
                                     searchedEndDate,
                                     onRecordCreated,
                                   }) {

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {

    e.preventDefault();

    setMessage("");

    try {

      setLoading(true);

      await createRecord({
        location_query: searchedLocation,
        start_date: searchedStartDate,
        end_date: searchedEndDate,
      });

      setMessage("✅ Weather record saved successfully!");

      if (onRecordCreated) {
        onRecordCreated();
      }

    }

    catch (error) {

      console.error(error);

      if (error.response) {
        setMessage(error.response.data.detail);
      }
      else {
        setMessage("Something went wrong.");
      }

    }

    finally {

      setLoading(false);

    }

  };

  return (

      <div className="bg-white rounded-xl shadow-lg p-6 mt-10">

        <h2 className="text-2xl font-bold mb-6">

          💾 Save Weather Record

        </h2>

        <form
            onSubmit={handleSubmit}
            className="space-y-5"
        >

          <div>

            <label className="font-semibold">

              📍 Location

            </label>

            <div className="w-full border rounded-lg p-3 mt-1 bg-gray-100 text-gray-700">

              {searchedLocation || "Search for a location first"}

            </div>

          </div>

          <div>

            <label className="font-semibold">

              📅 Start Date

            </label>

            <div className="w-full border rounded-lg p-3 mt-1 bg-gray-100 text-gray-700">

              {searchedStartDate || "-"}

            </div>

          </div>

          <div>

            <label className="font-semibold">

              📅 End Date

            </label>

            <div className="w-full border rounded-lg p-3 mt-1 bg-gray-100 text-gray-700">

              {searchedEndDate || "-"}

            </div>

          </div>

          <button

              type="submit"

              disabled={
                  loading ||
                  !searchedLocation ||
                  !searchedStartDate ||
                  !searchedEndDate
              }

              className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400"

          >

            {loading ? "Saving..." : "💾 Save Weather Record"}

          </button>

        </form>

        {message && (

            <p className="mt-5 font-semibold">

              {message}

            </p>

        )}

      </div>

  );

}
