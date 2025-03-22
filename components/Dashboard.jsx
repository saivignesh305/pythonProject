import { useEffect, useState } from "react";

export default function Dashboard() {
  const [stats, setStats] = useState({
    connections: 0,
    savedFromTheft: 0,
    users: 0
  });

  useEffect(() => {
    fetch("http://127.0.0.1:5000/fetch-stats")
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setStats({
            connections: data.connections || 0,
            savedFromTheft: data.savedFromTheft || 0,
            users: data.users || 0
          });
        }
      })
      .catch((error) => console.error("Error fetching stats:", error));
  }, []);

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-6">ARISTA VAULT</h1>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white shadow-md p-4 rounded-lg">
          <h2 className="text-gray-700 text-lg font-semibold">Connections</h2>
          <p className="text-2xl font-bold">{stats.connections}</p>
          <p className="text-sm text-green-600">12% increase</p>
        </div>

        <div className="bg-white shadow-md p-4 rounded-lg">
          <h2 className="text-gray-700 text-lg font-semibold">Saved from Theft</h2>
          <p className="text-2xl font-bold">{stats.savedFromTheft}</p>
          <p className="text-sm text-green-600">8% increase</p>
        </div>

        <div className="bg-white shadow-md p-4 rounded-lg">
          <h2 className="text-gray-700 text-lg font-semibold">Users</h2>
          <p className="text-2xl font-bold">{stats.users}</p>
          <p className="text-sm text-green-600">12% increase</p>
        </div>
      </div>
    </div>
  );
}
