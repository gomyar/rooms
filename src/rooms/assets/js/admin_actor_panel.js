
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
    for (var key in actor.state)
    {
        var value = actor.state[key];
        section.append(
            div("info").append(
                div("key", {'text': key}),
                div("value", {'text': value})
            )
        )
    }
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
