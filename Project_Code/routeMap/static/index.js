let map;
function htmlToElement(html) {
  var template = document.createElement('template');
  html = html.trim(); // Never return a text node of whitespace as the result
  template.innerHTML = html;
  return template.content.firstChild;
}

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 23.839310, lng: 120.951002 },
    zoom: 8,

    // UI
    zoomControl: false,
    streetViewControl: false,
    mapTypeControl:true,
    mapTypeControlOptions:{
      position: google.maps.ControlPosition.BOTTOM_CENTER,
    }
    // UI

  });
  

  // UI
  const controlDiv = document.createElement("div");
  const controlUI = document.createElement("button");
  var overlay;
  controlUI.classList.add("ui-button");
  controlUI.innerText = `213`;
  controlDiv.appendChild(controlUI);
  

  map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(controlDiv);

  map.controls[google.maps.ControlPosition.TOP_LEFT].push(htmlToElement(`
    <div id="left_dh"></div>`));

  map.controls[google.maps.ControlPosition.TOP_LEFT].push(htmlToElement(`
    <div id="header">
    <div class="dh_btn" onclick="openLeft_dh()">打开</div>
    <div class="user_admin_btn"></div>
    </div>`));

  // UI
    

    

  class USGSOverlay extends google.maps.OverlayView {
    bounds;
    image;
    div;
    constructor(bounds, image) {
      super();
      this.bounds = bounds;
      this.image = image;
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
    onRemove() {
      if (this.div) {
        this.div.parentNode.removeChild(this.div);
        console.log("asd");
        delete this.div;
      }
    }
  
  }

  google.maps.event.addListener(map, "idle", function() {
    // send the new bounds back to your server
    $.ajax({
      type:'GET',
      url:"box",
      data:{
        "bbox":map.getBounds() + ""
      },
      dataType:"json",
      success: function(data){
        const lbound = data["lbound"];
        const ubound = data["ubound"];
        const image = data["img"];

        const bounds = new google.maps.LatLngBounds(
          new google.maps.LatLng(lbound[1],lbound[0]),
          new google.maps.LatLng(ubound[1],ubound[0])
        );
        if(overlay)
          overlay.setMap(null);
        overlay = new USGSOverlay(bounds, image);
        overlay.setMap(map);
      }
  });
  });
  
  if(false){
    $.ajax({
        type:'GET',
        url:"data"+(imgId !== "None"?("Img?id="+imgId):""),
        dataType:"json",
        async: false,
        success: function(data){
          const lbound = data["lbound"];
          const ubound = data["ubound"];
          const image = data["img"];

          const bounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(lbound[1],lbound[0]),
            new google.maps.LatLng(ubound[1],ubound[0])
          );
      
          const overlay = new USGSOverlay(bounds, image);
          overlay.setMap(map);

        }
    });
  }
};

