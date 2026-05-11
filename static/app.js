const token = localStorage.getItem("music_token");

if (!token) {
    window.location.href = "/";
}

const trackForm = document.getElementById("trackForm");
const trackIdInput = document.getElementById("trackId");
const titleInput = document.getElementById("title");
const artistInput = document.getElementById("artist");
const albumInput = document.getElementById("album");
const genreInput = document.getElementById("genre");
const yearInput = document.getElementById("year");
const isHitInput = document.getElementById("isHit");

const formTitle = document.getElementById("formTitle");
const submitBtn = document.getElementById("submitBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const formMessage = document.getElementById("formMessage");

const tracksTableBody = document.getElementById("tracksTableBody");
const emptyMessage = document.getElementById("emptyMessage");
const searchInput = document.getElementById("searchInput");
const logoutBtn = document.getElementById("logoutBtn");


function showMessage(message, type) {
    formMessage.textContent = message;
    formMessage.className = "message " + type;

    setTimeout(() => {
        formMessage.textContent = "";
        formMessage.className = "message";
    }, 3000);
}


function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    };
}


function validateForm() {
    const title = titleInput.value.trim();
    const artist = artistInput.value.trim();
    const album = albumInput.value.trim();
    const genre = genreInput.value.trim();
    const year = yearInput.value.trim();
    const isHit = isHitInput.value === "true";

    if (!title || !artist || !album || !genre || !year) {
        showMessage("All fields are required.", "error");
        return null;
    }

    const yearNumber = Number(year);

    if (yearNumber < 1900 || yearNumber > 2100) {
        showMessage("Year must be between 1900 and 2100.", "error");
        return null;
    }

    return {
        title: title,
        artist: artist,
        album: album,
        genre: genre,
        year: yearNumber,
        is_hit: isHit
    };
}


async function loadTracks() {
    const search = searchInput.value.trim();
    let url = "/tracks";

    if (search) {
        url += "?search=" + encodeURIComponent(search);
    }

    const response = await fetch(url, {
        method: "GET",
        headers: getHeaders()
    });

    console.log("GET Tracks API Status Code:", response.status);

    if (response.status === 401) {
        localStorage.removeItem("music_token");
        window.location.href = "/";
        return;
    }

    const tracks = await response.json();
    renderTracks(tracks);
}


function renderTracks(tracks) {
    tracksTableBody.innerHTML = "";

    if (!tracks || tracks.length === 0) {
        emptyMessage.textContent = "No tracks found.";
        return;
    }

    emptyMessage.textContent = "";

    tracks.forEach(track => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${track.id}</td>
            <td>${escapeHtml(track.title)}</td>
            <td>${escapeHtml(track.artist)}</td>
            <td>${escapeHtml(track.album)}</td>
            <td>${escapeHtml(track.genre)}</td>
            <td>${track.year}</td>
            <td>${track.is_hit ? "🔥 Hit" : "Normal"}</td>
            <td>
                <button class="edit-btn" onclick="editTrack(
                    ${track.id},
                    '${escapeAttribute(track.title)}',
                    '${escapeAttribute(track.artist)}',
                    '${escapeAttribute(track.album)}',
                    '${escapeAttribute(track.genre)}',
                    ${track.year},
                    ${track.is_hit}
                )">Edit</button>

                <button class="delete-btn" onclick="deleteTrack(${track.id})">Delete</button>
            </td>
        `;

        tracksTableBody.appendChild(row);
    });
}


function editTrack(id, title, artist, album, genre, year, isHit) {
    trackIdInput.value = id;
    titleInput.value = title;
    artistInput.value = artist;
    albumInput.value = album;
    genreInput.value = genre;
    yearInput.value = year;
    isHitInput.value = isHit ? "true" : "false";

    formTitle.textContent = "Update Track";
    submitBtn.textContent = "Update Track";
    cancelEditBtn.style.display = "inline-block";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


async function createTrack(trackData) {
    const response = await fetch("/tracks", {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(trackData)
    });

    console.log("POST Create Track API Status Code:", response.status);

    const data = await response.json();

    if (response.ok) {
        showMessage("Track created successfully.", "success");
        resetForm();
        loadTracks();
    } else {
        showMessage(data.error || "Failed to create track.", "error");
    }
}


async function updateTrack(id, trackData) {
    const response = await fetch("/tracks/" + id, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify(trackData)
    });

    console.log("PUT Update Track API Status Code:", response.status);

    const data = await response.json();

    if (response.ok) {
        showMessage("Track updated successfully.", "success");
        resetForm();
        loadTracks();
    } else {
        showMessage(data.error || "Failed to update track.", "error");
    }
}


async function deleteTrack(id) {
    const confirmDelete = confirm("Are you sure you want to delete this track?");

    if (!confirmDelete) {
        return;
    }

    const response = await fetch("/tracks/" + id, {
        method: "DELETE",
        headers: getHeaders()
    });

    console.log("DELETE Track API Status Code:", response.status);

    const data = await response.json();

    if (response.ok) {
        showMessage("Track deleted successfully.", "success");
        loadTracks();
    } else {
        showMessage(data.error || "Failed to delete track.", "error");
    }
}


trackForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const trackData = validateForm();

    if (!trackData) {
        return;
    }

    const trackId = trackIdInput.value;

    if (trackId) {
        await updateTrack(trackId, trackData);
    } else {
        await createTrack(trackData);
    }
});


function resetForm() {
    trackForm.reset();
    trackIdInput.value = "";
    isHitInput.value = "false";
    formTitle.textContent = "Add New Track";
    submitBtn.textContent = "Create Track";
    cancelEditBtn.style.display = "none";
}


cancelEditBtn.addEventListener("click", resetForm);

searchInput.addEventListener("input", loadTracks);

logoutBtn.addEventListener("click", function() {
    localStorage.removeItem("music_token");
    localStorage.removeItem("music_user");
    window.location.href = "/";
});


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function escapeAttribute(value) {
    return String(value)
        .replaceAll("\\", "\\\\")
        .replaceAll("'", "\\'")
        .replaceAll('"', "&quot;");
}


loadTracks();