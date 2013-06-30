
var admin_actor_panel = {};

admin_actor_panel.actor = null;
admin_actor_panel.gui = null;

admin_actor_panel.init = function(actor)
{
    $("#admin_actor_panel").empty();
    $("#admin_actor_panel").append(
        div("title", {'text': 'Selected Actor:'}),
        div("section").append(
            div("info").append(
                div("key", {'text': 'actor_type'}),
                div("value", {'text': actor.actor_type})
            ),
            div("info").append(
                div("key", {'text': 'name'}),
                div("value", {'text': actor.name})
            )
        ),
        div("title", {'text': 'State:'}),
        admin_actor_panel.state_section(actor),
        div("title", {'text': 'Inventory:'}),
        admin_actor_panel.inventory_section(actor)
    );
}

admin_actor_panel.state_section = function(actor)
{
    var section = div("section");
    admin_actor_panel.show_tree(section, actor.state);
    return section;
}

admin_actor_panel.inventory_section = function(actor)
{
    var section = div("section");
    if (actor.inventory)
        for (var key in actor.inventory)
        {
            var value = actor.inventory[key];
            section.append(
                div("info").append(
                    div("key", {'text': key}),
                    div("value", {'text': value})
                )
            )
        }
    else
        console.log("No Inventory");
    return section;
}

admin_actor_panel.show_tree = function(root_div, tree_data)
{
    tree_data['test'] = {
        'some': 12,
        'test': [
            123, 456
        ],
        'data': {
            'key1': 'val1',
            'key2': 'val2'
        }
    };
    var dyna_data = admin_actor_panel.build_tree(tree_data);
    root_div.dynatree({children: dyna_data, onSelect: admin_actor_panel.node_selected, checkbox: true, onActivate: admin_actor_panel.node_activated});
}

admin_actor_panel.build_tree = function(tree_data)
{
    var ulist = [];
    for (var key in tree_data)
    {
        var item = tree_data[key];
        var listitem = {title: key, hideCheckbox: true, icon: false};
        if (jQuery.type(item) != "object" && jQuery.type(item) != 'array')
            listitem.title = "<div>" + key + "</div>" + "<input type='text' value='"+item+"'></input>";
        if (jQuery.type(item) == "object" && !$.isEmptyObject(item))
            listitem.children = admin_actor_panel.build_tree(item);
        if (jQuery.type(item) == "array")
            listitem.children = admin_actor_panel.build_tree(item);
        ulist[ulist.length] = listitem;
    }
    return ulist;
}


admin_actor_panel.node_selected = function(selected, node)
{
    console.log("Selected:"+node + "="+selected);
}

admin_actor_panel.node_activated = function(node)
{
    console.log("Activated:"+node);
}
