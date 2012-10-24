

function init()
{
    console.log("init");
    $("#player_overlay").css("display", "none");

    gui.canvas = $("#screen")[0];
    $(gui.canvas).click(gui_game.canvas_clicked);
    $(gui.canvas).mousemove(gui_game.canvas_mousemove);

    $("#menu_quit").click(gui_game.menu_quit_clicked);
    $("#menu_inventory").click(gui_game.menu_inventory_clicked);
    $("#menu_scripts").click(admin.menu_scripts_clicked);

    $(window).resize(function() { gui.resetCanvas(); gui.draw(); });

    gui.resetCanvas();

    api_rooms.connect(gui_game.onmessage);

    loadImages(gui_assets.map_images, function() {
        gui_game.initBackgroundImage();
    });
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
    api_rooms.player_id = getParameter("player_id");
    api_rooms.instance_uid = getParameter("instance_uid");
    init();
}

$(document).ready(init_signin);

