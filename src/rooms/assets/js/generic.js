
var generic = {};

generic.gui = null;

generic.selected_actor = null;
generic.selected_actor_methods = {};
generic.player_commands = {};
generic.selected_input = null;

generic.Gui = function(root)
{
    this.root = root;
    this.player_commands = {};
}

function _info(title, text)
{
    return div("player_info").append(
        div("title", {"text": title}),
        div("value", {"text": text})
    );
}

generic.Gui.prototype.init = function()
{
    var gdiv = div("generic").append(
        div("section_title", {"text": "Player:"}),
        _info("name", api_rooms.player_actor.name),
        _info("type", api_rooms.player_actor.actor_type),
        _info("circle", api_rooms.player_actor.circle_id),
        _info("health", api_rooms.player_actor.health),
        _info("model", api_rooms.player_actor.model_type),
        _info("speed", api_rooms.player_actor.speed),
        div("section_title", {"text": "State:"}),
        this._state(),
        div("section_title", {"text": "Commands:"})
    );
    this.root.append(div("wrapper").append(gdiv));
    this.load_commands(gdiv);

    this.root.append(generic.Tree("test tree",
        [
            {'name': 'value'},
            {'name2': 'value2'},
            {"name3": {
                "inner1": "ivalue1",
                "inner2": {
                    "inner3": "here"
                },
                "inner3": [
                    { "inner1": "here1" },
                    { "inner2": "here2" }
                ]

            }},
            {'name': 'value'},
            {'name2': 'value2'},
            {"name3": {
                "inner1": "ivalue1",
                "inner2": {
                    "inner3": "here"
                },
                "inner3": [
                    { "inner1": "here1" },
                    { "inner2": "here2" }
                ]

            }},
            {'name': 'value'},
            {'name2': 'value2'},
            {"name3": {
                "inner1": "ivalue1",
                "inner2": {
                    "inner3": "here"
                },
                "inner3": [
                    { "inner1": "here1" },
                    { "inner2": "here2" }
                ]

            }}


        ]
    ));
}

generic.Gui.prototype._state = function()
{
    var player_state = div("player_state");
    for (key in api_rooms.player_actor.state)
    {
        player_state.append(div("player_info").append(
            div("title", {"text": key}),
            div("value", {"text": api_rooms.player_actor.state[key]})
        ));
    }
    return player_state;
}

generic.Gui.prototype.load_commands = function(gdiv)
{
    var self = this;
    api_rooms.call_command("api", {}, function(data) {
        for (i in data.commands)
        {
            self.player_commands[data.commands[i].name] = data.commands[i];
            self.player_commands[data.commands[i].name].values = {};
        }
        for (i in data.requests)
        {
            self.player_commands[data.requests[i].name] = data.requests[i];
            self.player_commands[data.commands[i].name].values = {};
        }
        self.show_api(data, gdiv)
    });
}

generic.Gui.prototype.show_api = function(data, root)
{
    console.log(data);
    for (command_id in data.commands)
        root.append(this.build_command(data.commands[command_id], "player_command"));
    for (command_id in data.requests)
        root.append(this.build_command(data.requests[command_id], "player_request"));
}


generic.Gui.prototype.actor_selected = function(actor)
{
    generic.selected_actor = actor;
    $(".actor_info").remove();
    this.root.append(this.actor_info(actor));
}


generic.Gui.prototype.actor_info = function(actor)
{
    var gdiv = div("generic actor_info").append(
        div("section_title", {"text": "Actor:"}),
        _info("name", actor.name),
        _info("type", actor.actor_type),
        div("section_title", {"text": "Commands:"})
    );
    this.root.append(div("target_wrapper").append(gdiv));
    this.load_methods(gdiv, actor);

    return gdiv;
}

generic.Gui.prototype.load_methods = function(gdiv, actor)
{
    var self = this;
    api_rooms.call_method(actor.actor_id, "api", {}, function(data) {
        self.selected_actor_methods = data;
        self.show_methods(data, gdiv)
    });
}

generic.Gui.prototype.build_command_fields = function(command_id)
{
    return this.player_commands[command_id].values;
}

generic.Gui.prototype.build_command = function(callable, classname)
{
    var self = this;
    var callable_div = div(classname);
    callable_div.append(
        div("callable_name", {"text": callable.name}).click(function() {
            self.call_command(callable.name, self.build_command_fields(callable.name));
        })
    );
    console.log("args:"+ callable.args);
    for (var arg = 1; arg < callable.args.length; arg ++)
    {
        var field_div = $("<input>", {'type':'text', 'class': 'field'});
        field_div.focus(function(){
            generic.selected_input = this;
        });
        field_div.attr("command_id", callable.name).attr("arg", callable.args[arg]).change(function(){
            console.log("changed "+$(this).attr("arg"));
            self.player_commands[$(this).attr("command_id")].values[$(this).attr("arg")] = $(this).val();
        });
        callable_div.append(
            div("arg", {"text": callable.args[arg]}),
            field_div
        );
    }
    return callable_div;
}

generic.Gui.prototype.call_command = function(command_id, kwargs)
{
    var self = this;
    api_rooms.call_command(command_id, kwargs, function(data) {
        console.log("Showing tree");
        $(".treeview_wrapper").remove();
        console.log("command:");
        console.log(data);
        self.root.append(generic.Tree(command_id +"()", data));
    });

}

generic.Gui.prototype.show_command_results = function(data)
{
    console.log("Showing tree");
    $(".treeview_wrapper").remove();
    this.root.append(generic.Tree("test tree", data));
}

generic.Gui.prototype.show_methods = function(data, root)
{
    console.log(data);
    for (command_id in data.commands)
        root.append(this.build_callable(data.commands[command_id], "player_command"));
    for (command_id in data.requests)
        root.append(this.build_callable(data.requests[command_id], "player_request"));
}


generic.Tree = function(name, data)
{
    return $("<div>", {"class": "treeview_wrapper"}).append(
        $("<div>", {'class': "treeview"}).append(
            div("name", {"text": name}),
            generic.Leaf(data)
        )
    );
}

generic.Leaf = function(data)
{
    if (typeof(data) == "object")
    {
        var dict_div = div("dict");
        for (key in data)
        {
            var item = data[key];
            if (typeof(item) == "string" || typeof(item) == "number" || typeof(item) == "boolean")
            {
                var field_div = div("field").append(
                    div("key", {"text": key}),
                    div("value", {"text": item})
                );
                field_div.attr("key", key);
                field_div.attr("value", item);
                dict_div.append(field_div.click(function(e){
                    var key = $(this).attr("key");
                    var value = $(this).attr("value");
                    console.log("Clicked "+key+" = "+value);
                }));
                var self = this;
                field_div.click(function(e){
                    if (generic.selected_input)
                        $(generic.selected_input).val($(this).attr("value"));
                });
            }
            else
            {
                dict_div.append(div("plusminus", {"text": "+"}));
                dict_div.append(div("dictentry").append(
                    div("dictkey", {"text": key}),
                    generic.Leaf(item)
                ));
            }
        }
        return dict_div;
    }
    else
        return div("value", {"text": "unknown"});
}
