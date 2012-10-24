
gui_inventory = {};

gui_inventory.InventoryScreen = function(inventory)
{
    this.inventory = inventory;
    this.div = this.create_gui();
} 

gui_inventory.InventoryScreen.prototype.create_gui = function()
{
    var div = $("<div>", {'class': 'inventory_list'});
    for (item_type in this.inventory)
    {
        div.append($("<div>", {'class': 'inventory_item', 'text': item_type}));
    }
    return div;
}
