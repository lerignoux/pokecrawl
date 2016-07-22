var mapContainerId = 'mapid'
var map;

window.onload = function() {
  displayMap(48.84166274475924, 2.362437632607799);
  ajax({
    method: 'GET',
    url: 'result.json'
  }, displayPokemons, () => { console.error("Could not fetch data") })

  ajax({
    method: 'GET',
    url: 'points.json'
  }, (data) => data.forEach(p => addMarker(map,p)))
}

function displayMap(lat, lon) {
  console.log('display')
  map = L.map(mapContainerId).setView([lat, lon], 13)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)
}

function displayPokemons(data) {
  console.log(data)
  map.setView([data.Latitude, data.Longitude], 13)
  data.Pokemons.forEach(p => addPokemonMarker(map, p))
}

function addPokemonMarker(map, markerInfo) {
  var marker = L.marker([markerInfo.Latitude, markerInfo.Longitude]).addTo(map)
  var expiration = markerInfo.Expiration ? new Date(markerInfo.Expiration) : undefined
  marker.bindPopup(
    "<b>" + markerInfo.Name +  "</b> # " + markerInfo.Number + "<br>" +
    (expiration ? "Expiration: " + expiration.toLocaleTimeString() : "")
  ).openPopup()
}


function addMarker(map, markerInfo) {
  var marker = L.marker([markerInfo.Latitude, markerInfo.Longitude]).addTo(map)
}

function ajax(endpoint, success, error) {
  var xhr = new XMLHttpRequest();
  xhr.open(endpoint.method, endpoint.url);
  xhr.addEventListener('load', function () {
    if (xhr.status === 200) {
      var response = null;
      try {
        response = JSON.parse(xhr.responseText);
      } catch (ignored) { }
      if (response !== null) success(response);
      else error !== undefined && error();
    } else error !== undefined && error();
  });
  xhr.send();
}