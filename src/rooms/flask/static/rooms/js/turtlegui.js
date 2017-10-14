
/** TurtleGUI - a javascript GUI library. Shared using MIT license (see LICENSE file)
*/

$.ajaxSetup ({
    // Disable caching of AJAX responses
    cache: false
});

var turtlegui = {};

turtlegui.root_element = $(document);


turtlegui._get_safe_value = function(elem, rel_data, datasrc) {
    var gres = elem.attr(datasrc);
    if (!gres) {
        throw "No " + datasrc + " field on element " + elem.attr('id');
    }
    return turtlegui._relative_eval(elem, gres);
}


turtlegui._relative_eval = function(elem, gres) {
    var rel = elem.data('data-rel');
    var switcharoo = {};
    for (var key in rel) {
        if (key in window) {
            switcharoo[key] = window[key];
        }
        window[key] = rel[key];
    }
    try {
        result = eval(gres);
    } catch(e) {
        try {
            console.log("Error at:");
            var getstack = function(elm) {
                return elm.parent().length > 0 && !elm.parent().is('body') ? getstack(elm.parent()).concat([elm]) : [elm];
            }
            var stack = getstack(elem);
            for (var i in stack) {
                var elm = $(stack[i]);
                var desc = elm.prop('nodeName') + (elm.attr('id')?'#'+elm.attr('id'):"") + "[" + elm.index() + "]";
                console.log("  ".repeat(i) + desc);
            }
            console.log("Error evaluating " + gres + " on elem : " + e);
        } catch (noconsole) {
            throw e;
        }
    } finally {
        for (var key in switcharoo) {
            window[key] = switcharoo[key];
        }
    }
    return result;
}


turtlegui.load_snippet = function(elem, url, rel_data) {
    elem.load(url, function(response, status, xhr) {
        if (status == 'success') {
            turtlegui.reload(elem, rel_data);
        } else {
            console.log("Could not load html snippet: " + url + " - " + xhr.status + " " + xhr.statusText);
        }
    });
}


turtlegui.reload = function(elem, rel_data) {
    if (!rel_data) rel_data = {};

    if (!elem) {
        elem = turtlegui.root_element;
    }
    if (rel_data) {
        elem.data('data-rel', rel_data);
    }
    if (elem.attr('data-gui-text')) {
        value = turtlegui._get_safe_value(elem, rel_data, 'data-gui-text');
        elem.text(value);
    }
    if (elem.attr('data-gui-class')) {
        var value = turtlegui._get_safe_value(elem, rel_data, 'data-gui-class');
        elem.addClass(value);
    }
    if (elem.attr('data-gui-id')) {
        var value = turtlegui._get_safe_value(elem, rel_data, 'data-gui-id');
        $(elem).attr('id', value);
    }
    if (elem.attr('data-gui-show')) {
        var value = turtlegui._get_safe_value(elem, rel_data, 'data-gui-show');
        if (value) {
            elem.show();
        } else {
            elem.hide();
            if (elem.attr('data-gui-id')) {
                $(elem).attr('id', null);
            }
            return;
        }
    }
    if (elem.attr('data-gui-click')) {
        elem.unbind('click').click(function() {
            return turtlegui._get_safe_value(elem, rel_data, 'data-gui-click');
        });
    }
    if (elem.attr('data-gui-list')) {
        var list = turtlegui._get_safe_value(elem, rel_data, 'data-gui-list');
        var rel_item = elem.attr('data-gui-item');
        var rel_key = elem.attr('data-gui-key');
        var orig_elems = elem.children();
        var first_elem = $(orig_elems[0]);
        first_elem.hide();
        var new_elems = [];
        for (var i in list) {
            var new_elem = $(first_elem).clone();
            new_elems[new_elems.length] = new_elem;
        }
        for (var i in new_elems) {
            var item = list[i];
            var new_elem = new_elems[i];
            elem.append(new_elem);
            new_elem.show();
            var rel_data = jQuery.extend({}, rel_data);
            rel_data[rel_item] = item;
            if (rel_key != null) {
                rel_data[rel_key] = i;
            }
            turtlegui.reload(new_elem, rel_data);
        }
        orig_elems.remove();
        elem.prepend(first_elem);
    }
    else if (elem.attr('data-gui-tree')) {
        var tree = turtlegui._get_safe_value(elem, rel_data, 'data-gui-tree');
        var rel_item = elem.attr('data-gui-nodeitem');

        var orig_elems = elem.children();
        var first_elem = $(orig_elems[0]);
        first_elem.hide();
        var rel_data = jQuery.extend({}, rel_data);
        rel_data[rel_item] = tree;
        rel_data['_last_tree_elem'] = first_elem;
        rel_data['_last_tree_item'] = rel_item;
         
        var new_elem = $(first_elem).clone();
        elem.append(new_elem);
        new_elem.show();
        turtlegui.reload(new_elem, rel_data);

        orig_elems.remove();
        elem.prepend(first_elem);
    }
    else if (elem.attr('data-gui-node')) {
        var node = turtlegui._get_safe_value(elem, rel_data, 'data-gui-node');

        var orig_elems = elem.children();
        var first_elem = rel_data['_last_tree_elem'];
        first_elem.hide();
        var rel_data = jQuery.extend({}, rel_data);
        rel_data[rel_item] = node;
        rel_data[rel_data['_last_tree_item']] = node;
 
        var new_elem = $(first_elem).clone();
        elem.append(new_elem);
        new_elem.show();
        turtlegui.reload(new_elem, rel_data);

        orig_elems.remove();
        elem.prepend(first_elem);
    }
    else if (elem.attr('data-gui-include') && !elem.attr('data-gui-included')) {
        elem.attr('data-gui-included', true);
        var url = elem.attr('data-gui-include');
        turtlegui.load_snippet(elem, url, rel_data);
    }
    else {
        elem.children().each(function() {
            turtlegui.reload($(this), rel_data);
        });
    }
    if (elem.attr('data-gui-val')) {
        var value = turtlegui._get_safe_value(elem, rel_data, 'data-gui-val');
        $(elem).val(value);
    }

    if (elem.attr('data-gui-change')) {
        var value = turtlegui._get_safe_value(elem, rel_data, 'data-gui-change');
        $(elem).unbind('change').change(value);
    }
}
