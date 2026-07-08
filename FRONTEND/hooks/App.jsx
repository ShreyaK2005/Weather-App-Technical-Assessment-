import { useState, useEffect } from "react";

import SearchBar from "./components/SearchBar";
import CurrentWeather from "./components/CurrentWeather";
import ForecastGrid from "./components/ForecastGrid";
import AQIUVCard from "./components/AQIUVCard";
import MapEmbed from "./components/MapEmbed";
import YoutubeEmbed from "./components/YoutubeEmbed";
import RecordForm from "./components/RecordForm";
import RecordsList from "./components/RecordsList";
import UpdateRecord from "./components/UpdateRecord";

import {
    getCurrentWeather,
    getRecords,
    getRecordsByLocation,
    updateRecord,
    deleteRecord
} from "./api/client";

function App() {

    const [weather, setWeather] = useState(null);
    const [records, setRecords] = useState([]);
    const [searchedLocation, setSearchedLocation] = useState("");
    const [searchedStartDate, setSearchedStartDate] = useState("");

    const [searchedEndDate, setSearchedEndDate] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [searchRecordLocation, setSearchRecordLocation] = useState("");
    const [selectedRecord,setSelectedRecord] = useState(null);


    const handleSearch = async (location, startDate, endDate) => {

        try {

            setLoading(true);
            setError("");

            const response = await getCurrentWeather(
                location,
                startDate,
                endDate
            );

            setWeather(response.data);

            setSearchedLocation(location);

            setSearchedStartDate(response.data.start_date);

            setSearchedEndDate(response.data.end_date);

        }

        catch (err) {

            console.error(err);

            if (Array.isArray(err.response?.data?.detail)) {

                setError(
                    err.response.data.detail[0].msg.replace("Value error, ", "")
                );

            } else {

                setError(
                    err.response?.data?.detail ||
                    "Date range invalid. Please try to keep dates to maximum 15 days."
                );

            }

        }

    };


    const handleCurrentLocation = () => {

        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        navigator.geolocation.getCurrentPosition(

            async (position) => {

                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                try {

                    setLoading(true);
                    setError("");

                    const response = await getCurrentWeather(
                        `${latitude},${longitude}`
                    );

                    setWeather(response.data);

                    setSearchedLocation(response.data.location.name);
                    setSearchedStartDate(response.data.start_date);
                    setSearchedEndDate(response.data.end_date);

                }

                catch (err) {

                    console.error(err);

                    setError("Could not get weather for your current location.");

                }

                finally {

                    setLoading(false);

                }

            },

            () => {

                alert("Location permission denied.");

            }

        );

    };

    const loadRecords = async (location = "") => {

        try {

            const response = await getRecords(location);

            setRecords(response.data);

        }

        catch (err) {

            console.error(err);

        }

    };

    useEffect(() => {
        loadRecords();
    }, []);



    const handleDelete = async (id) => {

        if (!window.confirm("Delete this record?")) return;

        try {

            await deleteRecord(id);

            loadRecords(searchRecordLocation);

        }

        catch (err) {

            console.error(err);

        }

    };

    const handleSelectRecord = (record) => {
        setSelectedRecord(record);
    };


    const handleUpdateRecord = async (id, data) => {

        try {

            await updateRecord(id, data);

            await loadRecords(searchRecordLocation);

            const response = await getCurrentWeather(
                data.location_query,
                data.start_date,
                data.end_date
            );

            setWeather(response.data);

            setSelectedRecord(null);

        }

        catch(err){

            console.error(err);

        }

    };



    return (

        <div className="min-h-screen bg-gray-100 px-4 py-6 md:px-10">

            <div className="text-center mb-10">

                <h1 className="text-4xl md:text-5xl font-bold">
                    🌤 PM Accelerator Weather Intelligence Platform
                </h1>

                <p className="mt-3 text-lg text-gray-700">
                    Built by <strong>Shreya Amol Kasture</strong>
                </p>

                <p className="mt-4 max-w-4xl mx-auto text-gray-600">
                    This intelligent weather platform provides current weather,
                    historical weather, customizable forecasts, air quality,
                    UV index, interactive maps, weather recommendations,
                    weather record management (CRUD),
                    PDF export, and location-aware forecasting
                    for informed decision-making.
                </p>

            </div>



            <SearchBar
                onSearch={handleSearch}
                onCurrentLocation={handleCurrentLocation}
            />

            {loading && (
                <div className="mt-6 text-center text-lg font-semibold">
                    Loading weather...
                </div>
            )}

            {error && (
                <div className="mt-6 text-center text-red-600 font-semibold">
                    {error}
                </div>
            )}

            {weather && (
                <>
                    <CurrentWeather weather={weather} />

                    <AQIUVCard weather={weather} />

                    <MapEmbed weather={weather} />

                    <YoutubeEmbed weather={weather} />

                    <ForecastGrid weather={weather} />


                    <RecordForm
                        searchedLocation={searchedLocation}
                        searchedStartDate={searchedStartDate}
                        searchedEndDate={searchedEndDate}
                        onRecordCreated={loadRecords}
                    />

                    <div className="mt-10 flex gap-4">

                        <button
                            onClick={() => loadRecords()}
                            className="bg-green-600 text-white px-6 py-3 rounded-lg"
                        >
                            View All Records
                        </button>



                        {selectedRecord && (

                            <UpdateRecord

                                record={selectedRecord}

                                onUpdate={handleUpdateRecord}

                                onCancel={()=>setSelectedRecord(null)}

                            />

                        )}



                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6 mt-8">

                        <h2 className="text-2xl font-bold mb-4">

                            Search Saved Records

                        </h2>

                        <div className="flex gap-4">

                            <input

                                type="text"

                                placeholder="Search by location"

                                value={searchRecordLocation}

                                onChange={(e)=>{

                                    setSearchRecordLocation(e.target.value);

                                    loadRecords(e.target.value);

                                }}

                                className="border rounded-lg p-3 flex-1"

                            />

                        </div>

                    </div>

                    <RecordsList
                        records={records}
                        onDelete={handleDelete}
                        onUpdate={handleSelectRecord}
                    />
                </>
            )}

            <footer className="text-center text-gray-500 mt-16 pb-6">

                PM Accelerator Assessment Submission

                <br />

                Developed by <strong>Shreya Amol Kasture</strong>

            </footer>
        </div>

    );

}

export default App;
