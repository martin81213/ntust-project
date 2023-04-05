const options = {
  fields: ["formatted_address", "geometry", "name"],
  strictBounds: false,
  types: ["establishment"],
};


//debug

var blockingroute = [];

let ICON;
var drawingManager;
var directionsService;
var directionsRenderer;
var geocoder;
let rectangle;
var rectangleDetector;
var directionsDisplay;
var routeResult = []; //to save the multiple routes
var map;

let startMarker = null;
let destMarker = null;
let eventPos = null; // form possition marker

var kde;  //kde picture object
var showKde = false; //show?
var showCurve = true; //show?
var showMor = false;

const morRow = 12
const morCol = 20
var morMap = new Array(morRow);
for (var i = 0; i < morMap.length; i++) {
  morMap[i] = new Array(morCol);
  for (var o = 0; o < morMap[i].length; o++) {
    morMap[i][o] = false;
  }
}
let currentRouteList = []; // polyline list
let currentGMWebList = [];


function initMap() {

  //const questionBtn = document.getElementById("createForm");
  // const footer_ = document.getElementById("footer_")
  // const functionBar = document.getElementById("controlButton");
  // const submitForm = document.getElementById("submit_");
  // submitForm.addEventListener("click", submittEvent);
  // Instantiate a directions service.
  directionsService = new google.maps.DirectionsService();
  directionsDisplay = new google.maps.DirectionsRenderer();

  const inBrowser = !inIframe();
  // cookie 
  if (inBrowser && (!getCookie('zoom') || !getCookie('center'))) {
    document.cookie = 'zoom = 13';
    document.cookie = 'center = (25.033367, 121.5595 )'
  }
  let zoom = inBrowser ? getCookie('zoom') : 13;
  let center = inBrowser ? getCookie('center').slice(1, -1).split(',') : [25.033367, 121.5595];


  // Create a map. mapOption is the control setting in ui.js
  map = new google.maps.Map(document.getElementById("map"), {
    
    zoom: parseInt(zoom),
    center: { lat: parseFloat(center[0]), lng: parseFloat(center[1]) },
    disableDefaultUI: true,
    // 衛星 地形圖
    mapTypeControl: false,
    mapTypeControlOptions: {
        style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
        position: google.maps.ControlPosition.TOP_LEFT ,
    },
 
    // 縮放
    scaleControl: true, // crtl + mouse
    zoomControl: true,  // button (+,-),

    // 拖動小人 街景服務
    streetViewControl: true,

    // 全螢幕化
    fullscreenControl: false,
  });
  const card = document.getElementById("pac-card");
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(card);

  

  // block frawing
  drawingManager = new google.maps.drawing.DrawingManager({
    drawingControl: false,
    drawingControlOptions: {
      drawingModes: [
        google.maps.drawing.OverlayType.RECTANGLE,
      ],
    },
    rectangleOptions: {
      strokeColor: "green",
      strokeWeight: 1,
      strokeOpacity: 1,
      editable: true,
      draggable: true,
      zIndex: 1,
    },
  });

  drawingManager.setMap(map);
  // block draw event
  google.maps.event.addListener(
    drawingManager,
    "overlaycomplete",
    function (event) {
      if (event.type == google.maps.drawing.OverlayType.RECTANGLE) {
        if (rectangle != null) rectangle.setMap(null);
        rectangle = event.overlay;
        var bounds = rectangle.getBounds();
        drawingManager.setDrawingMode(null);
        rectangleDetector = true;
      }
    }
  );
  // block draw event
  google.maps.event.addListener(
    drawingManager,
    "drawingmode_changed",
    function () {
      if (
        drawingManager.getDrawingMode() ==
        google.maps.drawing.OverlayType.RECTANGLE &&
        rectangle != null
      ) {
        rectangle.setMap(null);
        rectangleDetector = false;
      }
    }
  );

  // when the user clicks somewhere else on the map.
  google.maps.event.addListener(map, "click", function () {
    if (rectangle != null) rectangle.setMap(null);
    rectangleDetector = false;
  });

  document.getElementById('blockBtn').onclick = function () {
    drawingManager.setDrawingMode(google.maps.drawing.OverlayType.RECTANGLE);
  }

  // Create a renderer for directions and bind it to the map.



  ICON = {
    'BACKWARD_CLOSED_ARROW': google.maps.SymbolPath.BACKWARD_CLOSED_ARROW,
    'CIRCLE': google.maps.SymbolPath.CIRCLE
  }
  startMarker = placeDragMarker(null, 'CIRCLE', 'from');
  destMarker = placeDragMarker(null, 'BACKWARD_CLOSED_ARROW', 'to');
  eventPos = placeDragMarker(null, 'CIRCLE', 'eventPosition');

  startMarker.setMap(null);
  destMarker.setMap(null);
  eventPos.setMap(null);

  google.maps.event.addListener(eventPos, 'dragend', function (evt) {
    document.getElementById('eventLng').value = evt.latLng.lng();
    document.getElementById('eventLat').value = evt.latLng.lat();
  });

  // Display the route between the initial start and end selections.
  // Listen to change events from the start and end lists.
  const input1 = document.getElementById("from");
  const input2 = document.getElementById("to");
  const input3 = document.getElementById("eventPosition");
  const autocomplete1 = new google.maps.places.Autocomplete(input1, options);
  const autocomplete2 = new google.maps.places.Autocomplete(input2, options);
  const autocomplete3 = new google.maps.places.Autocomplete(input3, options);

  autocomplete1.addListener("place_changed", () => {
    const place = autocomplete1.getPlace();
    if (!place.geometry || !place.geometry.location) {
      // User entered the name of a Place that was not suggested and
      // pressed the Enter key, or the Place Details request failed.
      autocompleteService = new google.maps.places.AutocompleteService();
      autocompleteService.getPlacePredictions(
        {
          'input': place.name,
          'offset': place.name.length,
          'language': "zh-TW",
        },
        function listresult(list, status) {
          if (list == null || list.length == 0) {
            //google maps return empty list while user enter the place
          }
          else {
            // Here's the first result that the user saw
            // in the list. We can use it and it'll be just
            // as if the user actually selected it. 
            //But first we need to get its details
            placesService = new google.maps.places.PlacesService(document.getElementById('from'));
            placesService.getDetails(
              { 'reference': list[0].reference },
              function detailsresult(detailsResult, placesServiceStatus) {

                document.getElementById('from').value = (detailsResult.formatted_address);
                // Here's the first result in the AutoComplete with the exact
                // same data format as you get from the AutoComplete.
                startMarker.setPosition(detailsResult.geometry.location);
                startMarker.setMap(map);
              }
            );
          }
        }
      );
    }
    else {
      // The user selected a result from the list, we can 
      // proceed and use it right away
      startMarker.setPosition(place.geometry.location);
      startMarker.setMap(map);
    }
  }
  );

  autocomplete2.addListener("place_changed", () => {
    const place = autocomplete2.getPlace();
    if (!place.geometry || !place.geometry.location) {
      // User entered the name of a Place that was not suggested and
      // pressed the Enter key, or the Place Details request failed.
      autocompleteService = new google.maps.places.AutocompleteService();
      autocompleteService.getPlacePredictions(
        {
          'input': place.name,
          'offset': place.name.length,
          'language': "zh-TW",
        },
        function listresult(list, status) {
          if (list == null || list.length == 0) {
            //google maps return empty list while user enter the place
          }
          else {
            // Here's the first result that the user saw
            // in the list. We can use it and it'll be just
            // as if the user actually selected it. 
            //But first we need to get its details
            placesService = new google.maps.places.PlacesService(document.getElementById('to'));
            placesService.getDetails(
              { 'reference': list[0].reference },
              function detailsresult(detailsResult, placesServiceStatus) {
                document.getElementById('to').value = (detailsResult.formatted_address);
                // Here's the first result in the AutoComplete with the exact
                // same data format as you get from the AutoComplete.
                destMarker.setPosition(detailsResult.geometry.location);
                destMarker.setMap(map);
              }
            );
          }
        }
      );
    }
    else {
      // The user selected a result from the list, we can 
      // proceed and use it right away
      destMarker.setPosition(place.geometry.location);
      destMarker.setMap(map);
    }
  });

  // form input
  autocomplete3.addListener("place_changed", () => {
    const place = autocomplete3.getPlace();
    if (!place.geometry || !place.geometry.location) {
      // User entered the name of a Place that was not suggested and
      // pressed the Enter key, or the Place Details request failed.
      autocompleteService = new google.maps.places.AutocompleteService();
      autocompleteService.getPlacePredictions(
        {
          'input': place.name,
          'offset': place.name.length,
          'language': "zh-TW",
        },
        function listresult(list, status) {
          if (list == null || list.length == 0) {
            //google maps return empty list while user enter the place
          }
          else {
            // Here's the first result that the user saw
            // in the list. We can use it and it'll be just
            // as if the user actually selected it. 
            //But first we need to get its details
            placesService = new google.maps.places.PlacesService(document.getElementById('eventPosition'));
            placesService.getDetails(
              { 'reference': list[0].reference },
              function detailsresult(detailsResult, placesServiceStatus) {
                document.getElementById('eventPosition').value = (detailsResult.formatted_address);
                document.getElementById('addr').value=(detailsResult.formatted_address).replace(/[^\u4e00-\u9fa5]/gi, "");//傳中文地址給後端並去除不必要符號

                // Here's the first result in the AutoComplete with the exact
                // same data format as you get from the AutoComplete.
                // If the place has a geometry, then present it on a map.
                if (detailsResult.geometry.viewport) {
                  map.fitBounds(detailsResult.geometry.viewport);
                }
                // TODO:
                // change place.geometry.location to address -> latlng
                let pos = detailsResult.geometry.location;
                eventPos.setPosition(pos);
                eventPos.setMap(map);
                // init pos
                document.getElementById('eventLng').value = pos.lng();
                document.getElementById('eventLat').value = pos.lat();
              }
            );
          }
        }
      );
    }
    else {
      // If the place has a geometry, then present it on a map.
      if (place.geometry.viewport) {
        map.fitBounds(place.geometry.viewport);
      }
      document.getElementById('addr').value=place.formatted_address.replace(/[^\u4e00-\u9fa5]/gi, "");//傳中文地址給後端並去除不必要符號
  
      // TODO:
      // change place.geometry.location to address -> latlng
      let pos = place.geometry.location;
      eventPos.setPosition(pos);
      eventPos.setMap(map);
      // init pos
      document.getElementById('eventLng').value = pos.lng();
      document.getElementById('eventLat').value = pos.lat();
    }
  });

  // picture class
  class USGSOverlay extends google.maps.OverlayView {
    bounds;
    image;
    div;
    constructor(bounds, image, show = true) {
      super();
      this.bounds = bounds;
      this.image = image;
      this.isShow = show;
    }
    /**
     * onAdd is called when the map's panes are ready and the overlay has been
     * added to the map.
     */
    onAdd() {
      this.div = document.createElement("div");
      this.div.style.borderStyle = "none";
      this.div.style.borderWidth = "0px";
      this.div.style.position = "absolute";

      // Create the img element and attach it to the div.
      const img = document.createElement("img");

      img.src = this.image;
      img.style.width = "100%";
      img.style.height = "100%";
      img.style.position = "absolute";
      this.div.appendChild(img);

      // Add the element to the "overlayLayer" pane.
      const panes = this.getPanes();

      panes.overlayLayer.appendChild(this.div);

      if (!this.isShow) {
        this.hide();
      }
    }
    draw() {
      // We use the south-west and north-east
      // coordinates of the overlay to peg it to the correct position and size.
      // To do this, we need to retrieve the projection from the overlay.
      const overlayProjection = this.getProjection();
      // Retrieve the south-west and north-east coordinates of this overlay
      // in LatLngs and convert them to pixel coordinates.
      // We'll use these coordinates to resize the div.
      const sw = overlayProjection.fromLatLngToDivPixel(
        this.bounds.getSouthWest()
      );
      const ne = overlayProjection.fromLatLngToDivPixel(
        this.bounds.getNorthEast()
      );

      // Resize the image's div to fit the indicated dimensions.
      if (this.div) {
        this.div.style.left = sw.x + "px";
        this.div.style.top = ne.y + "px";
        this.div.style.width = ne.x - sw.x + "px";
        this.div.style.height = sw.y - ne.y + "px";
      }
    }
    /**
     * The onRemove() method will be called automatically from the API if
     * we ever set the overlay's map property to 'null'.
     */
    hide() {
      if (this.div) {
        this.div.style.visibility = "hidden";
      }
    }
    show() {
      if (this.div) {
        this.div.style.visibility = "visible";
      }
    }
    onRemove() {
      if (this.div) {
        this.div.parentNode.removeChild(this.div);
        delete this.div;
      }
    }
    toggle() {
      if (this.div) {
        if (this.div.style.visibility === "hidden") {
          this.show();
        } else {
          this.hide();
        }
      }
    }
  }


  var dataLatLngToAddr=[];
  var dataId=[];
  var afterLatLng=[];
  var sendMess=[];


  async function getGeoCoder(evt){
    return new Promise(resolve => {
      geocoder
        .geocode({'latLng':evt})
        .then(async (results) => {
          console.log(results);
          resolve(results); ///使用非同步的方法取值
        })
        .catch((e) => {
          alert("Geocode was not successful for the following reason: " + e);
        });
    });
  }
 
  ///////////////////////////////////
  // kde button
  const kdeButton = document.getElementById("kde_")
  kdeButton.addEventListener("click", () => {
    showKde = !showKde;
    if (showKde) {
      loadKde();
    }
    else { // clean last one
      removeKde();
    }
  });

  // mor button
  const morButton = document.getElementById("mor_")
  $("#mor_").on("click", () => {
    showMor = !showMor;
  });


  function toMorMapIndex(lnglat) {
    return [Math.floor((lnglat.lng() - 120.01930) / 0.1802), Math.floor((lnglat.lat() - 21.86400) / 0.1802)]
  }
  // load mor image when drag
  google.maps.event.addListener(map, "drag", function () {
    var ub, lb;
    ub = toMorMapIndex(map.getBounds().getNorthEast());
    lb = toMorMapIndex(map.getBounds().getSouthWest());
    for (var i = lb[0]; i <= ub[0]; i++) {
      for (var o = lb[1]; o <= ub[1]; o++) {
        if (i >= 0 && i < morRow && o >= 0 && o < morCol && morMap[i][o] === false) {
          morMap[i][o] = true;
          getImage(i + '_' + o + '_' + 2);
        }
      }
    }
  });

  let changetm = null;
  // dragend event show kde 
  google.maps.event.addListener(map, "center_changed", function () {
    // send request if center stop over 200ms
    clearTimeout(changetm);
    changetm = setTimeout(center_changed_handle, 200);
  });
  function center_changed_handle() {
    if (showKde) {
      loadKde();
    }
    else { // clean last one
      removeKde();
    }
    if (inBrowser) {
      // save pos to cookie
      document.cookie = "zoom=" + map.getZoom();
      document.cookie = "center=" + map.getCenter();
    }
  }



  function loadKde() {
    // send the new bounds back to server
    $.ajax({
      type: 'POST',
      url: "/box",
      data: {
        "bbox": map.getBounds() + "",
        'csrfmiddlewaretoken': getCookie('csrftoken')
      },
      dataType: "json",
      success: function (data) {
        const lbound = data["lbound"];
        const ubound = data["ubound"];
        const image = data["img"];

        const bounds = new google.maps.LatLngBounds(
          new google.maps.LatLng(lbound[1], lbound[0]),
          new google.maps.LatLng(ubound[1], ubound[0])
        );
        if (kde) // clean last one
          kde.setMap(null);
        kde = new USGSOverlay(bounds, image); // new one
        kde.setMap(map);
      }
    });
  }
  function removeKde() {
    // clear kde picutue
    if (kde) {
      kde.setMap(null);
      kde = null;
    }
  }
  function getImage(id, deferr = null) {
    // special postion
    $.ajax({
      type: "GET",
      url:  "/dataImg",
      data: { "id": id },
      dataType: "json",
      success: function (response) {
        const lbound = response["lbound"];
        const ubound = response["ubound"];
        const image = response["img"];

        const bounds = new google.maps.LatLngBounds(
          new google.maps.LatLng(lbound[1], lbound[0]),
          new google.maps.LatLng(ubound[1], ubound[0])
        );

        var pic = new USGSOverlay(bounds, image, showMor);
        pic.setMap(map);

        morButton.addEventListener("click", () => {
          pic.toggle();
        });

        if (deferr)
          deferr.resolve(pic);
      },
      error: function (error) {
        console.log("getImage error:", error);
      },

    });

  }

  geocoder = new google.maps.Geocoder();

} // initMap


function SendBlockPolyline(start_, end_, block_) {
  start_ = start_.results[0].geometry.location
  end_ = end_.results[0].geometry.location
  $.ajaxSettings.async = false;
  blockPump = 'bbox:' + block_.sw_.lng() + ',' + block_.ne_.lat() + ',' + block_.ne_.lng() + ',' + block_.sw_.lat();
  start_tmp = start_.lat() + ',' + start_.lng();
  end_tmp = end_.lat() + ',' + end_.lng();

  $.ajax({
    type: "POST",
    url: "/road_block",
    dataType:'json',
    data: { 
      origin: start_tmp, 
      destination: end_tmp, 
      block: blockPump, 
      alternatives: `3`,
      'csrfmiddlewaretoken': getCookie('csrftoken')
    },
    success: function (response) {
      var colors = ["#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"];
      let colorIdx = 0;
      currentRouteList = []
      currentGMWebList = []
      for (let i = 0; i < response['pointList'].length; i++) {
        let latlngs = [];
        response['pointList'][i].forEach(function (latLng) {
          latlngs.push({ lat: latLng[0], lng: latLng[1] });
        })
        // console.log('response: ', response)
        rectangleDetector = true
        currentGMWebList.push(getRoadWebsite(latlngs,rectangleDetector));
        currentRouteList.push(google.maps.geometry.encoding.encodePath(latlngs));
        let dr = new google.maps.DirectionsRenderer({
          suppressInfoWindows: true,
          suppressMarkers: true,
          polylineOptions: {
            strokeColor: colors[colorIdx++ % 4],
          },
          map: map,
        });
        routeResult.push({ 'route': null, 'curve': [] });
        routeResult[i]['route'] = dr;

        var begin = 0;
        response['curve'][i].forEach(function (value) {
          let end = begin + value[0];
          var color = "";
          if (value[1] == 0) {
            color = "#7FFF00";//green
          }
          else if (value[1] == 1) {
            color = "#FFA500";//orange
          }
          else {
            color = "#FF4500";//red
          }
          // draw line
          const path = new google.maps.Polyline({
            path: latlngs.slice(begin, end + 1),
            geodesic: true,
            strokeColor: color,
            strokeWeight: 8,
          });

          path.setMap(map);
          begin = end;
          routeResult[i]['curve'].push(path); //add to list
        });
      }

      showDangerousPage(response['dangerDeg']);
    },
    error: function (error) {
      alert("failed");
    },
  });
}

function RouteCurve(poly) {
  // road curve dangerous
  if (showCurve) {
    $.ajax({
      type: "POST",
      url:  "/curve",
      data: { 
        polyline: poly + '',
        'csrfmiddlewaretoken': getCookie('csrftoken') },
      success: function (response) {
        var res = JSON.parse(response);
        res.forEach(function (signalPath, i) {
          var point_list = google.maps.geometry.encoding.decodePath(poly[i]);
          var begin = 0;

          signalPath.forEach(function (value) {
            let end = begin + value[0];
            var color = "";
            if (value[1] == 0) {
              color = "#7FFF00";//green
            }
            else if (value[1] == 1) {
              color = "#FFA500";//orange
            }
            else {
              color = "#FF4500";//red
            }
            // draw line
            const path = new google.maps.Polyline({
              path: point_list.slice(begin, end + 1),
              geodesic: true,
              strokeColor: color,
              strokeWeight: 8,
            });

            path.setMap(map);
            begin = end;
            routeResult[i]['curve'].push(path); //add to list
          });
        })
      },
      error: function (error) {
        console.log("RouteCurve error:", error);
      },
    });
  }
}

function routeKDE(poly) {

  $.ajax({
    type: "POST",
    url:  "/dangerous",
    data: { polyline: poly,'csrfmiddlewaretoken': getCookie('csrftoken')},
    dataType: 'json',
    success: function (response) {
      showDangerousPage(response['dangerDeg']);
    },
    error: function (error) {
      console.log("RouteKDE error:", error);
    },
  });

}

function calcRoute() {
  clearRoutes();
  // First, remove any existing markers from the map.
  let from = document.getElementById("from");
  let to = document.getElementById("to");
  if (!from.value && !to.value) {
    window.alert("No input");
    return;
  }

  if (rectangleDetector) {
    // use block route api
    const ne_ = rectangle.getBounds().getNorthEast();
    const sw_ = rectangle.getBounds().getSouthWest();
    blockRec = { ne_, sw_ };
    let start;
    let dest;
    start = document.getElementById("from");
    dest = document.getElementById("to");
    transferAddrtoLatlng(start, dest, blockRec);
  }
  else {
    // use google route api

    // Retrieve the start and end locations and create a DirectionsRequest using
    // WALKING directions.
    directionsService
      .route({
        origin: from.value,
        destination: to.value,
        travelMode: google.maps.TravelMode.DRIVING,
        provideRouteAlternatives: true,
      })
      .then((result) => {
        // Route the directions and pass the response to a function to create
        // markers for each step.

        var colors = ["#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"];
        let colorIdx = 0;

        // show route in map
        currentRouteList = []
        currentGMWebList = []
        // console.log(result)
        for (let i = 0; i < result.routes.length; i++) {
          // saved the google map navigation website of route 
          currentGMWebList.push(getRoadWebsite(result.routes[i],rectangleDetector));
          currentRouteList.push(result.routes[i].overview_polyline)
          let dr = new google.maps.DirectionsRenderer({
            suppressInfoWindows: true,
            suppressMarkers: true,
            polylineOptions: {
              strokeColor: colors[colorIdx++ % 4],
            },
            map: map,
          });
          dr.setDirections(result); // Tell the DirectionsRenderer which route to display
          dr.setRouteIndex(i);
          dr.setMap(map);

          routeResult.push({ 'route': null, 'curve': [] });
          routeResult[i]['route'] = dr;
        }

      
        RouteCurve(currentRouteList); // road curve dangerous
        routeKDE(JSON.stringify(currentRouteList)); // road_dangerous
      })
      .catch((e) => {
        window.alert("Directions request failed due to " + e);
      });
  }
}

function clearRoutes() {
  /*
      clear route list
  */
  routeResult.forEach(function (e) {
    e['route'].setMap(null);
    e['curve'].forEach(function (c) {
      c.setMap(null);
    });
  })
  routeResult = [];
}

function getRoadWebsite(roadInfo, rectangleDetector) {

  // // 先確認使用者裝置能不能抓地點
  // if(navigator.geolocation) {

  // // 使用者不提供權限，或是發生其它錯誤
  // function error() {
  //   alert('無法取得你的位置');
  // }

  // // 使用者允許抓目前位置，回傳經緯度
  // function success(position) {
  //   console.log('current position: ',position.coords.latitude, position.coords.longitude);
  // }

  // // 跟使用者拿所在位置的權限
  // navigator.geolocation.getCurrentPosition(success, error);
  // // var point_list = google.maps.geometry.encoding.decodePath(roadInfo.overview_polyline);
  // // console.log(point_list);

  if (rectangleDetector){
    
    // console.log('where getRoadWebsite(arg...) called by SendBlockPolyline, that parameter-roadinfo is: ', roadInfo)
    const stepMod = 1 + Math.floor(roadInfo.length / 8)
    
    var web = 'https://www.google.com.tw/maps/dir/'
    web += roadInfo[0]['lat'] + ',' + roadInfo[0]['lng']+ '/'

    for (let i = 0; i < roadInfo.length; i += stepMod) {
      // console.log('step ',i,' latlngs:',roadInfo[i]['lat'],', ', roadInfo[i]['lng'])
      web += roadInfo[i]['lat']+ ',' + roadInfo[i]['lng'] + '/'
    }

    web += roadInfo[roadInfo.length-1]['lat'] + ',' + roadInfo[roadInfo.length-1]['lng']+ '/'
    web += '@' + roadInfo[roadInfo.length-1]['lat'] + ',' +roadInfo[roadInfo.length-1]['lng'] + '/'

    return web
  }
  else{
    //google.maps.LatLng
    const myRoute = roadInfo.legs[0];
    var web = 'https://www.google.com.tw/maps/dir/'

    web += myRoute.start_location.lat() + ',' + myRoute.start_location.lng() + '/'
    const stepMod = 1 + Math.floor(myRoute.steps.length / 7)
    for (let i = 0; i < myRoute.steps.length; i += stepMod) {
      web += myRoute.steps[i].end_location.lat() + ',' + myRoute.steps[i].end_location.lng() + '/'
    }
    web += myRoute.end_location.lat() + ',' + myRoute.end_location.lng() + '/'
    web += '@' + myRoute.end_location.lat() + ',' + myRoute.end_location.lng() + '/'

    return web
  }
  // } else {
  //     alert('Sorry, 你的裝置不支援地理位置功能。')
  // }
}





function htmlToElement(html) {
  /*
      html text to element
  */
  var template = document.createElement('template');
  html = html.trim(); // Never return a text node of whitespace as the result
  template.innerHTML = html;
  return template.content.firstChild;
}

function getCookie(name) {
  /*
    get cookie
  */
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function inIframe() {
  /*
    check self in iframe
   */
  try {
    return window.self !== window.top;
  } catch (e) {
    return true;
  }
}

function placeMarker(latlng, title = "Macker") {
  /*
    place normal marker with title

   */
  return new google.maps.Marker({
    position: latlng,
    map,
    title: title,
  });
}


function placeDragMarker(initPos = null, iconType = 'CIRCLE', result = '') {
  /*
    place draggable marker

      iconType: str, ICON key 
      result: str, html element id

      Return: marker
   */
  let marker = new google.maps.Marker({
    position: initPos === null ? map.getCenter() : initPos,
    icon: {
      path: ICON[iconType],
      scale: 8,
    },
    map: this.map,
    animation: google.maps.Animation.DROP,
    draggable: true,
  });

  if (result !== '') {
    google.maps.event.addListener(marker, 'dragend', function (evt) {
      geocoder.geocode({ 'latLng': evt.latLng }, function (results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
          document.getElementById('addr').value=(results[1].formatted_address).replace(/[^\u4e00-\u9fa5]/gi, "");//傳中文地址給後端並去除不必要符號
          document.getElementById(result).value = (results[1].formatted_address);
        }
      });
    });
  }
  return marker
}

async function transferAddrtoLatlng(s, t, b) {
  s = await addrtolatlng({ address: s.value });
  t = await addrtolatlng({ address: t.value });
  SendBlockPolyline(s, t, b);
}
async function addrtolatlng(request) {
  return new Promise(resolve => {
    geocoder
      .geocode(request)
      .then(async (results) => {
        resolve(results); ///使用非同步的方法取值
      })
      .catch((e) => {
        alert("Geocode was not successful for the following reason: " + e);
      });

  });
}


function setCurve(routeResult) {
  const curveTarget = showCurve ? map : null;
  const routeTarget = showCurve ? null : map;
  routeResult.forEach(function (e) {
    e['route'].setMap(routeTarget);
    e['curve'].forEach(function (c) {
      c.setMap(curveTarget);
    });
  })
}

