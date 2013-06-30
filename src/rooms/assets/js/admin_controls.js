
var admin_controls = {};

admin_controls.init = function()
{
    $("#controls").append(
        div("control").append(
            $("<input>", {'type': 'checkbox', 'id': 'show_visible'}).change(function(){
                gui.draw_invisible_actors = $('#show_visible').is(":checked");
                gui.requestRedraw();
            }),
            div("text", {'text': 'Show invisible actors'})
        )
    );
}
