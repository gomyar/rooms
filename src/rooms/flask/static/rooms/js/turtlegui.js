
/**
    Requires Jquery 1.x or greater 
    To use:
    1. Create html template using data-gui-* tags
    2. Populate json object data (manually or using an ajax call).
        var my_data = {'name': 'Turtle Soup', 'ingredients': [{'name': 'water'}, {'name': 'turtle'}]}
    3. Turtlegui evaluates js strings, i.e. "my_data.name" is used to populate 
    4. Whenever a change occurs (data load or user change), call:
        turtlegui.reload()
       which reloads the gui
    4. The html on the page will be populated with the loaded data, as per template.

    Example html template:

    -----
    <html>
    <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha256-ZosEbRLbNQzLpnKIkEdrPv7lOy9C27hHQ+Xp8a4MxAQ=" crossorigin="anonymous"></script>
    <script src="turtlegui.js"></script>
    <script>
    var my_data = {
        'restaurant': {
            'name': 'Turtle Soup',
            'ingredients': [
                {'name': 'water'},
                {'name': 'turtle'}
            ]
        }
    };

    function i_was_clicked(item) {
        var index = jQuery.inArray(item, my_data.restaurant.ingredients);
        alert("Ingredient: " + index + "->" + item.name);
    }

    function last_updated(item) {
        return new Date();
    }

    function add_ingredient() {
        my_data.restaurant.ingredients.push({'name': 'salt'});
        turtlegui.reload()
    }

    function remove_ingredient(item) {
        var index = jQuery.inArray(item, my_data.restaurant.ingredients);
        my_data.restaurant.ingredients.splice(index, 1);
        turtlegui.reload()
    }

    function get_title_class(e, item) {
        return "title";
    }

    $(document).ready(function() {
        turtlegui.reload()
    });
    </script>
    <style>
        div.title {
           font-weight : bold;
        }
    </style>
    <body>
        <div data-gui-text="my_data.restaurant.name"></div>    <!-- refers to 'name' field in data -->
        <div data-gui-list="my_data.restaurant.ingredients" data-gui-item="ingredient">   <!-- gui-list iterates over 'ingredients' list, stores each in 'ingredient' variable -->
            <div>
                <div data-gui-text="ingredient.name"></div>   <!-- 'ingredient' set for each item in list -->
                <input type="button" data-gui-click="i_was_clicked(ingredient)" value="Info"></input>   <!-- function called with item -->
                <input type="button" data-gui-click="remove_ingredient(ingredient)" value="Remove"></input>
                <div data-gui-text="last_updated(ingredient)"></div>   <!-- text from function -->
            </div>
        </div>
        <input type='button' onclick='add_ingredient()' value='Add'></input>
    </body>
    </html>
    -----

    Turtlegui uses "data-" element fields which resolve js, (function call or dot notation path to data)

    Types of supported fields:
        data-gui-text: populates element.text() with the evaluated value
        data-gui-list: creates copies of its subelement, one for each item in the list, stores item as local variable, as named by field 'data-gui-item'
        data-gui-show: shows or hides based on evaluated value (true/false)
        data-gui-click: evaluates js on click (normally a function call)
        data-gui-include: include an html snippet
        data-gui-class: sets classname(s) on element
        data-gui-val: sets value on element

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
    result = eval(gres);
    for (var key in switcharoo) {
        window[key] = switcharoo[key];
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
