

function init()
{
    console.log("init");

    gui.canvas = $("#screen")[0];
    gui.init_input();

    admin_controls.init();
    logpanel.init();
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

            api_rooms.load_room(function(data){
                console.log("Room loaded");
                gui.viewport_x = api_rooms.room.width / 2;
                gui.viewport_y = api_rooms.room.height / 2;
                gui.zoom = 1.05 * api_rooms.room.height / gui.canvas.height;
                gui.actorRedraw();
            });
        }
        if (message.command == "actor_update")
            gui.actorRedraw();
        if (message.command == "debug")
        {
            console.log("debug: "+message.kwargs.msg);
            logpanel.add_log(message.kwargs.actor_id, "debug", message.kwargs.time, message.kwargs.msg);
        }
        if (message.command == "exception")
        {
            console.log("exception: "+message.kwargs.msg);
            logpanel.add_log(message.kwargs.actor_id, "exception", message.kwargs.time, message.kwargs.msg, message.kwargs.stacktrace);
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
