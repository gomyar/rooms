var gui_sprite = {};

function distance(x1, y1, x2, y2)
{
    return Math.sqrt((x2-x1)^2, (y2-y1)^2);
}

gui_sprite.Sprite = function(id)
{
    this.id = id;
    this.path = [ [ 0.0, 0.0, api_rooms.get_now() ], [ 0.0, 0.0, api_rooms.get_now() ] ];
    this.width = 50;
    this.height = 50;
    this.selected = false;
    this.hovered = false;
}


gui_sprite.Sprite.prototype.set_model = function(model)
{
    this.model = model;
    this.img = images[this.model];
}

gui_sprite.Sprite.prototype.is_walking = function()
{
    return api_rooms.get_now() < this.path[this.path.length-1][2] * 1000;
}

gui_sprite.Sprite.prototype.draw = function(ctx)
{
    if (this.hovered == true && this != api_rooms.own_actor)
        gui.draw_rect(this.x()-2-this.width/2, this.y()-2-this.height/2,
            this.width + 4, this.height + 4, "rgb(0,200,0)");
    gui.draw_text_centered(this.x(), this.y() - this.height / 2, this.id);

    vector = this.current_vector();

    var angle = Math.atan2(vector[1][1] - vector[0][1],
        vector[1][0] - vector[0][0]);

    if (this.is_walking())
        offset = Math.round((new Date().getTime() % 1400) / 200);
    else
        offset = 0;

    ctx.save();
    ctx.translate(this.x(), this.y());

    if (this.speech != null)
    {
        console.log("Drawing speech:"+this.speech);
        gui.ctx.fillStyle='#ffffff';
        gui.ctx.beginPath();
        gui.ctx.moveTo(0, -50);
        gui.ctx.lineTo(10, -50);
        gui.ctx.lineTo(0, -40);
        gui.ctx.lineTo(0, -50);
        gui.ctx.closePath();
        gui.ctx.fill();

        gui.fill_text_centered(0, -50, this.speech);
    }

    ctx.rotate(angle);
    ctx.translate(- this.width / 2, - this.height / 2);
    ctx.drawImage(this.img, 0, offset * 50, 50, 50, 0, 0, 50, 50);
    ctx.restore();
}

gui_sprite.Sprite.prototype.current_vector = function()
{
    now = api_rooms.get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
        return [ this.path[this.path.length-2], this.path[this.path.length-1] ];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    var start_point = this.path[index];
    var end_point = this.path[index + 1];

    return [ start_point, end_point ];
}

gui_sprite.Sprite.prototype.end_time = function()
{
    return this.path[this.path.length-1][2] * 1000;
}

gui_sprite.Sprite.prototype.x = function()
{
    now = api_rooms.get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
        return this.path[this.path.length-1][0];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    start_x = this.path[index][0];
    start_y = this.path[index][1];
    start_time = this.path[index][2] * 1000;
    end_x = this.path[index + 1][0];
    end_y = this.path[index + 1][1];
    end_time = this.path[index + 1][2]* 1000;

    now = api_rooms.get_now();
    if (now > end_time)
        return end_x;
    diff_x = end_x - start_x;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_x;
    inc = (now - start_time) / diff_t;
    return start_x + diff_x * inc;
}

gui_sprite.Sprite.prototype.y = function()
{
    now = api_rooms.get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
        return this.path[this.path.length-1][1];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    start_x = this.path[index][0];
    start_y = this.path[index][1];
    start_time = this.path[index][2] * 1000;
    end_x = this.path[index + 1][0];
    end_y = this.path[index + 1][1];
    end_time = this.path[index + 1][2]* 1000;

    now = api_rooms.get_now();
    if (now > end_time)
        return end_y;
    diff_y = end_y - start_y;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_y;
    inc = (now - start_time) / diff_t;
    return start_y + diff_y * inc;
}

gui_sprite.Sprite.prototype.optionalRedraw = function()
{
    if (gui.redraw_until <= this.end_time())
    {
        gui.redraw_until = this.end_time();
        gui.requestRedraw();
    }
}

gui_sprite.Sprite.prototype.time_till = function(start_x, start_y, end_x, end_y)
{
    x = start_x;
    y = start_y;
    console.log("till: "+x+","+y+" "+end_x+","+end_y);
    dist = distance(x, y, end_x, end_y);
    console.log("dist:"+dist);
    return dist / 1000;
}

gui_sprite.Sprite.prototype.atPosition = function(x, y)
{
    x1 = this.x() - this.width / 2;
    y1 = this.y() - this.height / 2;
    x2 = x1 + this.width;
    y2 = y1 + this.height;
    return x > x1 && x < x2 && y > y1 && y < y2;
}

gui_sprite.Sprite.prototype.select = function()
{
    this.selected = true;
    if (this.id == api_rooms.player_id)
        api_rooms.exposed_commands(this.id, gui_game.show_commands);
    else
        api_rooms.exposed_methods(this.id, gui_game.show_commands);
}

gui_sprite.Sprite.prototype.deselect = function()
{
    this.selected = false;
}

gui_sprite.Sprite.prototype.speech_bubble = function(msg)
{
    var self = this;
    if (this.speech_timeout != null)
        clearTimeout(this.speech_timeout);
    this.speech = msg;
    this.speech_timeout = setTimeout(function() {
        self.speech = null;
        gui.requestRedraw();
    }, 3000);
}
