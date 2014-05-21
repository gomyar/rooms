
var image_map = {
    'player': '/assets/images/character_models/player.png',
    'npc': '/assets/images/character_models/npc.png'
}

// Thank you stackoverflow
function getParameter(paramName)
{
    var searchString = window.location.search.substring(1),
    i, val, params = searchString.split("&");

    for (var i=0;i<params.length;i++)
    {
        val = params[i].split("=");
        if (val[0] == paramName)
        {
        return unescape(val[1]);
        }
    }
    return null;
}

function api_callback(message)
{
    console.log("API Message:");
    console.log(message);
    gui.actorRedraw();
}

function init()
{
    console.log("Loading images");
    guiassets.loadImages(image_map, function() {
        console.log("Loaded images");
        gui.initCanvas($("#screen")[0]);
        api_rooms.connect(getParameter("game_id"), getParameter("username"), getParameter("token"), api_callback); 
    });
}


$(document).ready(init);
