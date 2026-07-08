export default function AQIUVCard({ weather }) {

  if (!weather) return null;

  if (!weather.air_quality) {
    return (
        <div className="bg-white rounded-xl shadow-lg p-6 mt-8 text-center">
          <h2 className="text-2xl font-bold mb-4">
            🌫 Air Quality
          </h2>

          <p>
            Air quality data is only available for the current weather.
          </p>
        </div>
    );
  }

  const airQuality = weather.air_quality;

  return (

      <div className="grid grid-cols-1 md:grid-cols-2 mt-8">


        <div className="bg-white rounded-xl shadow-lg p-6">

          <h2 className="text-2xl font-bold mb-4">
            🌫 Air Quality
          </h2>

          {airQuality ? (

              <>
                <p><strong>AQI:</strong> {airQuality.european_aqi}</p>
                <p><strong>Status:</strong> {airQuality.status}</p>
                <p><strong>PM2.5:</strong> {airQuality.pm2_5}</p>
                <p><strong>PM10:</strong> {airQuality.pm10}</p>
                <p><strong>CO:</strong> {airQuality.carbon_monoxide}</p>
                <p><strong>NO₂:</strong> {airQuality.nitrogen_dioxide}</p>
                <p><strong>Ozone:</strong> {airQuality.ozone}</p>

                <div className="mt-4 text-green-700 text-center">
                  {airQuality.health_advice}
                </div>

              </>

          ) : (

              <p className="text-gray-500">
                Air quality data is only available for the current weather.
              </p>

          )}


        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">

          <h2 className="text-2xl font-bold mb-4">

            ☀ UV Index

          </h2>

          <div className="text-5xl font-bold mb-4">

            {weather.uv_index}

          </div>

          <p>

            {weather.uv_advice}

          </p>

        </div>

      </div>

  );

}
