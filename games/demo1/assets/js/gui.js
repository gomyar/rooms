
var gui = {};

gui.canvas = null;
gui.ctx = null;

gui.redraw_until = 0;
gui.walk_timeout = 0;

gui.viewport_x = 0;
gui.viewport_y = 0;

gui.resetCanvas = function()
{
    gui.canvas.width = $("#main").width();
    gui.canvas.height = $("#main").height();
    gui.ctx=gui.canvas.getContext("2d");
}

gui.draw = function()
{
    gui.ctx.clearRect(0, 0, gui.canvas.width, gui.canvas.height);
    if (gui_assets.background_img != null)
        gui.ctx.drawImage(gui_assets.background_img, gui.viewport_x, gui.viewport_y);

    gui.ctx.save()
    if (api_rooms.own_actor != null)
    {
        gui.viewport_x = -(api_rooms.own_actor.x() - gui.canvas.width / 2);
        gui.viewport_y = -(api_rooms.own_actor.y() - gui.canvas.height / 2);
        gui.ctx.translate(gui.viewport_x, gui.viewport_y);
    }


    gui_game.draw_room();


    for (var i in gui_game.sprites)
        gui_game.sprites[i].draw(gui.ctx);

    gui.ctx.restore();

    if (api_rooms.get_now() < gui.redraw_until)
        gui.requestRedraw();

    gui.draw_text_centered(200, 20, "("+parseInt(gui.viewport_x)+", "+parseInt(gui.viewport_y)+")", "black");
}

gui.requestRedraw = function()
{
    setTimeout(gui.draw, 20);
}

gui.draw_rect = function(x, y, width, height, color)
{
    gui.ctx.strokeStyle = color;
    gui.ctx.beginPath();
    gui.ctx.rect(x, y, width, height);
    gui.ctx.closePath();
    gui.ctx.stroke();
}

gui.fill_rect = function(x, y, width, height, color)
{
    gui.ctx.fillStyle = color;
    gui.ctx.fillRect(x, y, width, height);
}

gui.draw_text_centered = function(x, y, text, color)
{
    gui.ctx.font="10px Arial";
    var metrics = gui.ctx.measureText(text);
    var width = metrics.width;
    gui.ctx.fillText(text, x - width / 2, y - 5);
}

gui.fill_text_centered = function(x, y, text, color, fillColor)
{
    gui.ctx.font="10px Arial";
    if (color == null) color = "#000000";
    if (fillColor == null) fillColor = "#ffffff";
    var metrics = gui.ctx.measureText(text);
    var width = metrics.width;
    gui.ctx.fillStyle=fillColor;
    gui.ctx.fillRect(x - width / 2 - 5, y - 15, width + 10, 15);
    gui.ctx.fillStyle=color;
    gui.ctx.fillText(text, x - width / 2, y - 5);
}



