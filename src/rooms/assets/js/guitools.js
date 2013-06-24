var guitools = {};

function div(classname, options) {
    var createoptions = $.extend({'class': classname}, options);
    var element = $("<div>", createoptions);
    return element
};


// I can't remember what this is for...
(function( $ ){
    $.fn.buttonClick = function(obj, func, args) {
        return this.click({'obj': obj, 'func': func, 'args': args}, function(e){
            var obj = e.data.obj;
            var func = e.data.func;
            var args = e.data.args;
            console.log("Calling "+func+"("+args+")"+" with");
            console.log(obj);
            func.apply(obj, args);
        });
    };
    $.fn.append_elements = function(elements) {
        for (var i in elements)
            this.append(elements[i]);
        return this;
    };
})( jQuery );


scrollable = function(inner)
{
    this.div = div("scrollable").append(inner);
    inner.resize(this.resized);
    return this.div
}

scrollable.prototype.resized = function(e)
{
    console.log("resized");
    console.log(e);
}

guitools.center_div = function(div)
{
    var parent = div.offsetParent();
    var coords = div.offset();
    if (coords.top + div.height() > parent.height())
        coords.top = parent.height() - div.height() - 2;
    if (coords.top < 0)
        coords.top = 0;
    if (coords.left + div.width() > parent.width())
        coords.left = parent.width() - div.width() - 2;
    if (coords.left < 0)
        coords.left = 0;
    div.offset(coords);
}
