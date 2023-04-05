/*
    Read me !!!
    ## menu manager
        menuManager.push(callbackClass)
        menuManager.pop()
    ## callbackClass
        onShow: call when show page
        onHide: call when hide page
        onRemove: call when pop page
*/

class menuControl {
    constructor() {
        this.stack = [];
        this.menu = new menuCallback('leftMenu');
        this.mainPage = new baseCallback('main_panel');
        this.isOpen = false;
    }
    push(callbackItem) {
        if (this.stack.length > 0) {
            // hide current page
            this.hide(this.currentPage());
        }
        else {
            // open left menu
            this.show(this.menu);
        }
        // push
        this.stack.push(callbackItem);
      
        this.show(callbackItem);
        this.changeButtonIcon();

    }
    pop() {
        const len = this.stack.length;
        if (len > 0) {
            let item = this.stack.pop();
            this.hide(item);
            item.onRemove();
            if (len == 1) {
                // close left menu
                this.hide(this.menu);
            }
            else {
                // show previous page
                this.show(this.currentPage());
                this.changeButtonIcon();
            }
        }
    }
    changeButtonIcon() {
        if (this.stack.length > 1) {
            // change button to back icon
            document.getElementById('controlButton-icon').className = 'fa fa-arrow-left';
        }
        else {
            // change button to close icon
            document.getElementById('controlButton-icon').className = 'fa fa-times';
        }
    }
    len() {
        return this.stack.length;
    }
    currentPage() {
        return this.stack[this.stack.length - 1];
    }
    show(item) {
        item.onShow();
    }
    hide(item) {
        item.onHide();
    }
}

class baseCallback {
    // show, hide
    constructor(id) {
        this.id = id;
    }
    onShow() {
        document.getElementById(this.id).style.display = 'block';
    }
    onHide() {
        document.getElementById(this.id).style.display = 'none';
    }
    onRemove() {
    }
}

class formCallback extends baseCallback {
    // remove marker on map
    constructor(id) {
        super(id);
    }
    onHide() {
        eventPos.setMap(null);
        super.onHide();
    }

}
class menuCallback extends baseCallback {
    // left menu animation
    constructor(id) {
        super(id);
    }
    onShow() {
        this.isOpen = true;
        document.getElementById('leftMenu').classList.toggle('leftMenu-show');
    }
    onHide() {
        this.isOpen = false;
        document.getElementById('leftMenu').classList.remove('leftMenu-show');
    }

}

class templateCallback extends baseCallback {
    // remove self when pop from stack
    constructor(id) {
        super(id);
    }
    onRemove() {
        document.getElementById(this.id).remove();
    }
}

class routeCallback extends templateCallback {
    // show, hide route 
    constructor(id, route) {
        super(id);
        this.route = [];
        Object.assign(this.route, route); // copy route
    }
    onShow() {
        super.onShow();
        if (this.route.length > 0 && this.route[0]['route'])
            setCurve(this.route); // show
    }
    onHide() {
        super.onHide();
        if (this.route.length > 0 && this.route[0]['route'])
            this.route.forEach(function (e) { // remove
                e['route'].setMap(null);
                e['curve'].forEach(function (c) {
                    c.setMap(null);
                });
            })
    }
}

class eventCallback extends routeCallback {
    // show, hide markers
    constructor(id, markers, route) {
        super(id, route);
        this.markers = markers;
    }
    onShow() {
        super.onShow();
        this.markers.forEach(function (v) {
            v.setMap(map);
        })
    }
    onHide() {
        super.onHide();
        this.markers.forEach(function (v) {
            v.setMap(null);
        })
    }
}

let menuManager = new menuControl();

let serialId = 0;
$(document).ready(function () {
    menuManager.push(menuManager.mainPage);

    $('#createForm').click(function () {
        menuManager.push(new formCallback('formPage'));
    });

    $('#controlButton').click(function () {
        // previous page button
        menuManager.pop();
    });


    $('#menuBtn').click(function () {
        if (menuManager.isOpen) {
            // hide
            menuManager.hide(menuManager.menu);
        }
        else {
            // show
            if (menuManager.len() == 0) {
                // push main_panel
                menuManager.push(menuManager.mainPage);
            }
            else {
                menuManager.show(menuManager.menu);
            }
        }
    });

    $('#showAllPointsBtn').click(function () {
        $.ajax({
            type: 'GET',
            url:  "/getAllPoints",
            dataType: 'json',
            success: function (data) {
                showEventPage(data)
            }
        });
    });
    // ajaxform
    $('#eventForm').ajaxForm({
        beforeSubmit: function (arr, $form, options) {
            return true;
        },
        success: function (data) {
            menuManager.pop();
            clearFormInput(); // clear forn
        },
        error: function () {
            alert('upload failed...');
        }
    });

    // prevent default enter evnet
    document.getElementById("eventPosition").addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });
});


function showDangerousPage(valueList) {
    // input valueList: list  dangerous for each route

    // template
    let pageTemp = document.getElementById("routePageTemplate");
    let page = pageTemp.content.cloneNode(true);
    let id = 'routePage' + serialId++;
    page.querySelector('.MenuContent').id = id;

    // content
    var temp = page.querySelector("#routeItemTemplate");
    valueList.forEach((v, i) => {
        // list
        var clon = temp.content.cloneNode(true);
        clon.querySelector('.routeItem').setAttribute("index", i);

        clon.querySelector('.routeItem-word').textContent = 'Road  ' + (i + 1) + '\n危險:' + v.toFixed(1);

        let btn = clon.querySelector('.routeItem-showEventButton');
        btn.onclick = getEventPoint;
        btn.setAttribute('polyline', currentRouteList[i])

        let gobtn = clon.querySelector('.routeItem-goButton');
        gobtn.setAttribute('link', currentGMWebList[i])
        gobtn.onclick = function () {/// click button to open the Google Map navigation web
            window.open(this.getAttribute('link'), 'route navigation website');
        }

        // append to list
        page.querySelector('.routeList').appendChild(clon);
    });

    document.getElementById('leftMenu').appendChild(page);
    menuManager.push(new routeCallback(id, routeResult));
}

function getEventPoint() {
    // route_page show btn click event

    // index of route
    let index = this.parentElement.getAttribute('index');
    $.ajax({
        type: 'POST',
        url: "/listRelatedPoint",
        data: {
            'polyline': this.getAttribute('polyline'),
            'csrfmiddlewaretoken': getCookie('csrftoken')
        },
        dataType: "json",
        success: function (data) {
            showEventPage(data, index)
        }
    });
}

function showEventPage(valueList, index = null) {
    /*
    input list
    {
        popularNum: int
        position: [lng(float), lat(float)]
        title: str
        time: str(yyyy-MM-dd hh:mm)
        county: str, value same as select options on the form
        situation: int, value same as select options on the form
    }
    */
    let pageTemp = document.getElementById("eventPageTemplate");
    let page = pageTemp.content.cloneNode(true);
    let id = 'eventPointPage' + serialId++;
    page.querySelector('.MenuContent').id = id;
    page.querySelector('.fullSelect').style.display='block';
    // content
    var temp = page.querySelector('#eventItemTemplate');
    let markers = []
    valueList.forEach((v, i) => {
        // list
        var clon = temp.content.cloneNode(true);
        clon.querySelector('.eventItem').setAttribute('index', i);

        let title = clon.querySelector('.eventItem-title');
        title.textContent = v['title'];
        title.onclick = getEventDetail;
        title.setAttribute('eventId', v['id']);
        title.setAttribute('county',v['physicalAddr']);
        title.setAttribute('situation',v['situation']);

        clon.querySelector('.eventItem-pushNum').textContent = v['popularNum'];
        color = '';
        if (v['popularNum'] >= 100) 
            color = '#F84D41';
        else if (v['popularNum'] >= 10) 
            color = '#F7C100';
        else if (v['popularNum'] > 0) 
            color = '#48BF84';
        else 
            color = '#393939'
        clon.querySelector('.eventItem-pushNum').setAttribute("style", "color:" + color);

        clon.querySelector('.eventItem-time').textContent = v['time'].replace(' ', '\n');

        // create marker
        markers.push(placeMarker({
            "lng": v['position'][0],
            "lat": v['position'][1]
        }, v['title']));
        markers[i].addListener("click", () => {
            markers[i].setAnimation(google.maps.Animation.BOUNCE);
            setTimeout(function () { markers[i].setAnimation(null); }, 7500);
            title.click();
        })
        // append
        page.querySelector(".eventList").appendChild(clon);
    });
    document.getElementById('leftMenu').appendChild(page);

    let route = index != null ? [menuManager.currentPage().route[index]] : [];
    menuManager.push(new eventCallback(id, markers, route));

    document.querySelector(".Taiwan").addEventListener("change",queryEvent);
    document.querySelector(".TaiSituation").addEventListener("change",queryEvent);
    
}
function queryEvent(){
    ///Get the selection value and list will have all the event we saved
    let county = this.parentElement.children[0].value;
    let situation = Number(this.parentElement.children[1].value);
    let list = this.parentElement.parentElement.getElementsByClassName('eventItem');

    ///copare_county and compared_situation are the value we get from the list above
    ///we will have the 4 situation 
    ///separate from all county and all situation, specific county and all situation,
    ///all county and specific event, specific county and specific event
    ///after the situation and county being confirmed, we will show the event wanted and set the markers
    for (let i =0;i<list.length;i++) {
        // let eventId = list[i].children[0].getAttribute('eventid');
        let compare_county = list[i].children[0].getAttribute('county');
        let compare_situation=parseInt((list[i].children[0].getAttribute('situation')), 10)+1;
        if(county=="全台"&&(situation==0||compare_situation==situation)){
            list[i].style.display= "block";
            menuManager.currentPage().markers[i].setMap(map);
        }
        else if(compare_county.indexOf(county)!=-1&&(situation==0||situation==compare_situation)){
            list[i].style.display= "block";
            menuManager.currentPage().markers[i].setMap(map);
        }
        else{
            list[i].style.display= "none";
            menuManager.currentPage().markers[i].setMap(null);
        }
    }
}

function getEventDetail() {
    // title click event
    // index of event page)
    let index = parseInt(this.parentElement.getAttribute('index'));
    $.ajax({
        type: 'GET',
        url:  "/getPointInfo",
        data: {
            "id": parseInt(this.getAttribute('eventId')),
        },
        dataType: "json",
        success: function (data) {
            showDetailPage(data, index);
        }
    });
}
function showDetailPage(value, index) {
    // detail page
    /*
    RootObject {
        id:         int
        coordinate: [lng,lat];
        startDate:  yyyy/MM/dd hh:mm
        isSlove:    number;
        popularNum: number;
        situaName:  string;
        posterName: string;
        remark:     string;
    } 
    */

    // template
    let pageTemp = document.getElementById("detailPageTemplate");
    let page = pageTemp.content.cloneNode(true);
    let id = 'eventDetailPage' + serialId++;
    page.querySelector('.MenuContent').id = id;
    page.querySelector('.MenuContent').setAttribute('eventId', value['id']);
    // content
    page.querySelector('div[name = "detail-title"]').textContent = value['situaName'];
    page.querySelector('div[name = "detail-time"]').textContent = value['startDate'];
    page.querySelector('div[name = "detail-poster"]').textContent = value['posterName'];
    page.querySelector('div[name = "detail-describe"]').textContent = value['remark'];
    if (value['picLink'] !== ''){
        piclink = `../media/${value['picLink']}`;
        page.querySelector('img').setAttribute('src', piclink);
    }
    let pushBtn = page.querySelector('button[name = "detail-pushBtn"]');
    pushBtn.onclick = modifyPopularNum;
    pushBtn.name = value['id'];
    let solveBtn = page.querySelector('button[name = "detail-solveBtn"]');
    solveBtn.onclick = solvePoint;
    solveBtn.name = value['id'];

    // append
    document.getElementById('leftMenu').appendChild(page);

    let route = menuManager.currentPage().route ? menuManager.currentPage().route : [];
    let marker = [menuManager.currentPage().markers[index]];
    menuManager.push(new eventCallback(id, marker, route))

}


function dropStartPosMar() {
    if (startMarker.map !== null) {
        startMarker.setMap(null);
    }
    else {
        startMarker.setPosition(map.getCenter())
        startMarker.setMap(map);
    }
}

function dropDestPosMar() {
    if (destMarker.map !== null) {
        destMarker.setMap(null);
    }
    else {
        destMarker.setPosition(map.getCenter())
        destMarker.setMap(map);
    }
}

function markerShow() {
    if (eventPos.map !== null) {
        eventPos.setMap(null);
    }
    else {
        eventPos.setPosition(map.getCenter());
        eventPos.setMap(map);
    }
}

function clearFormInput() {
    document.getElementById('situaName').value = '';
    document.getElementById('posterName').value = '';
    document.getElementById('eventPosition').value = '';
    document.getElementById('remark').value = '';
    document.getElementById('picLink').value = '';
    document.getElementById('eventLng').value = '0';
    document.getElementById('eventLat').value = '0';
    $("#preview_progressbarTW_img").attr('src', '#');
}

function modifyPopularNum() {
    $.ajax({
        type: 'POST',
        url:  "/modifyPopularNum",
        data: {
            "id": this.name,
            'csrfmiddlewaretoken': getCookie('csrftoken')
        },
        success: function (data) {
            // TODO: success event
        }
    });
}

function solvePoint() {
    $.ajax({
        type: 'POST',
        url:  "/solvePoint",
        data: {
            "id": this.name,
            'csrfmiddlewaretoken': getCookie('csrftoken')
        },
        success: function (data) {
            // TODO: success event
        }
    });
}