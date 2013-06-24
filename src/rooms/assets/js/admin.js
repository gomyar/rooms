

function init()
{
    console.log("init");

    gui.canvas = $("#screen")[0];
    gui.init_input();
//    generic.gui = new generic.Gui($("#main"));

//    $("#menu_quit").click(gui_game.menu_quit_clicked);
//    $("#menu_inventory").click(gui_game.menu_inventory_clicked);

    $(window).resize(function() { gui.resetCanvas(); gui.draw(); });

    gui.resetCanvas();

    api_rooms.connect(onmessage);
}

function onmessage(msg)
{
    var messages = jQuery.parseJSON(msg.data);
    for (var i in messages)
    {
        var message = messages[i];
        if (message.command == "sync")
        {
            console.log("Sync: "+message.kwargs.actors.length+" actors");
            console.log(message);

            api_rooms.load_room(function(data){console.log("Room loaded");});
            gui.viewport_x = api_rooms.player_actor.x();
            gui.viewport_y = api_rooms.player_actor.y();
            gui.actorRedraw();
        }
    }
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

function init_signin()
{
    console.log("init signin");
    api_rooms.token = getParameter("token");
    init();
}

$(document).ready(init_signin);
