
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

canvas_clicked = function(e)
{
    var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));
    console.log("clicked "+click_x+","+click_y);

    var player_actor = api_rooms.player_actors()[0];
    api_rooms.call_command(player_actor.actor_id, "move_to", { x: click_x, y: click_y });
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
        $("#screen").click(canvas_clicked);
        api_rooms.connect(getParameter("game_id"), getParameter("username"), getParameter("token"), api_callback); 
    });
}


$(document).ready(init);
