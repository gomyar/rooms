
var guiassets = {};

guiassets.images = {};

guiassets.loadImages = function(imagemap, callback)
{
    var count = 0;
    for (i in imagemap)
    {
        var image = new Image();
        image.src = imagemap[i];
        image.onload = function () {
            count --;
            if (count <= 0)
                callback();
        };
        guiassets.images[i] = image;
        count ++;
    }
}

