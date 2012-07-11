
function Sprite(id)
{
    this.id = id;
    this.path = [ [ 0.0, 0.0, get_now() ], [ 0.0, 0.0, get_now() ] ];
    this.width = 50;
    this.height = 50;
    this.selected = false;
    this.hovered = false;
}

Sprite.prototype.set_model = function(model)
{
    this.model = model;
    this.img = images[this.model];
}

Sprite.prototype.is_walking = function()
{
    return get_now() < this.path[this.path.length-1][2] * 1000;
}

Sprite.prototype.is_animating = function()
{
    return get_now() < this.action.end_time * 1000;
}

Sprite.prototype.draw = function(ctx)
{
    if (this.hovered == true)
        draw_rect(this.x()-2-this.width/2, this.y()-2-this.height/2,
            this.width + 4, this.height + 4, "rgb(200,200,0)");
    if (this.selected == true)
        draw_rect(this.x()-2-this.width/2, this.y()-2-this.height/2,
            this.width + 4, this.height + 4, "rgb(0,200,0)");

    vector = this.current_vector();

    angle = Math.atan2(vector[1][1] - vector[0][1],
        vector[1][0] - vector[0][0]);

    if (this.is_walking())
    {
        offset = Math.round((new Date().getTime() % 1400) / 200);
    }
    else if (this.is_animating())
    {
        console.log("Animating!!!!!");
        offset = Math.round((new Date().getTime() % 700) / 100);
    }
    else
    {
        offset = 0;
    }

    ctx.save();
    ctx.translate(this.x(), this.y());

    ctx.rotate(angle);
    ctx.translate(- this.width / 2, - this.height / 2);
    ctx.drawImage(this.img, 0, offset * 50, 50, 50, 0, 0, 50, 50);
    ctx.restore();
}

Sprite.prototype.current_vector = function()
{
    now = get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
        return [ this.path[this.path.length-2], this.path[this.path.length-1] ];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    var start_point = this.path[index];
    var end_point = this.path[index + 1];

    return [ start_point, end_point ];
}

Sprite.prototype.end_time = function()
{
    return this.path[this.path.length-1][2] * 1000;
}

Sprite.prototype.x = function()
{
    now = get_now();
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

    now = get_now();
    if (now > end_time)
        return end_x;
    diff_x = end_x - start_x;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_x;
    inc = (now - start_time) / diff_t;
    return start_x + diff_x * inc;
}

Sprite.prototype.y = function()
{
    now = get_now();
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

    now = get_now();
    if (now > end_time)
        return end_y;
    diff_y = end_y - start_y;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_y;
    inc = (now - start_time) / diff_t;
    return start_y + diff_y * inc;
}

Sprite.prototype.optionalRedraw = function()
{
    if (redraw_until <= this.end_time())
    {
        redraw_until = this.end_time();
        requestRedraw();
    }
}

Sprite.prototype.time_till = function(start_x, start_y, end_x, end_y)
{
    x = start_x;
    y = start_y;
    console.log("till: "+x+","+y+" "+end_x+","+end_y);
    dist = distance(x, y, end_x, end_y);
    console.log("dist:"+dist);
    return dist / 1000;
}

Sprite.prototype.atPosition = function(x, y)
{
    x1 = this.x() - this.width / 2;
    y1 = this.y() - this.height / 2;
    x2 = x1 + this.width;
    y2 = y1 + this.height;
    return x > x1 && x < x2 && y > y1 && y < y2;
}

Sprite.prototype.select = function()
{
    this.selected = true;
    if (this.id == player_id)
        service_call("/game/" + instance_uid + "/" + this.id + "/exposed_commands", {}, show_commands);
    else
        service_call("/game/" + instance_uid + "/" + this.id + "/exposed_methods", {}, show_commands);

}

Sprite.prototype.deselect = function()
{
    this.selected = false;
}

Sprite.prototype.clicked = function()
{
    console.log("Sprite "+this.id+" clicked");
}
