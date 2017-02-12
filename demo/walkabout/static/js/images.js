
var gameimages = {};

gameimages.images = {};

gameimages.loadImages = function(imagemap, callback)
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
        gameimages.images[i] = image;
        count ++;
    }
}

