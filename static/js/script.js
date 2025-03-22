document.addEventListener("DOMContentLoaded", function () {
    fetch("/data")
        .then(response => response.json())
        .then(data => updateDashboard(data))
        .catch(error => console.error("Error fetching data:", error));
});

function updateDashboard(data) {
    const usersContainer = document.getElementById("users");
    const trackersContainer = document.getElementById("trackers");

    usersContainer.innerHTML = "";
    trackersContainer.innerHTML = "";

    Object.entries(data.users).forEach(([uid, user]) => {
        const userCard = document.createElement("div");
        userCard.classList.add("card");
        userCard.innerHTML = `
            <h3>${user.name}</h3>
            <p>Email: ${user.email}</p>
            <p>Device: ${user.deviceType}</p>
            <p>Last Login: ${user.lastLogin}</p>
        `;
        usersContainer.appendChild(userCard);
    });

    Object.entries(data.trackers_detail).forEach(([uid, trackerData]) => {
        Object.entries(trackerData.devices).forEach(([mac, device]) => {
            const trackerCard = document.createElement("div");
            trackerCard.classList.add("card");
            trackerCard.innerHTML = `
                <h3>${device.customDeviceName}</h3>
                <p>Device Type: ${device.deviceType}</p>
                <p>Connection Status: ${device.connectionStatus}</p>
                <p>Connected Count: ${device.connectedCount}</p>
            `;
            trackersContainer.appendChild(trackerCard);
        });
    });
}