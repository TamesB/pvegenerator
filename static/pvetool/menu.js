var hamburger = document.getElementById("hamburger");
var menu_left = document.getElementById("menu_left");
var menu_links = document.getElementsByClassName("menu_link");
var article = document.getElementById("article");

hamburger.addEventListener("click", function() {
    this.classList.toggle("active")
    toggle_menu(this, menu_links, article, menu_left);

})

function toggle_menu(element, menu_links, article, menu_left) {
    if (element.classList.contains("active")) {
        menu_left.style.flex = "0 0 15%;"
        menu_left.style.minWidth = "15vw";
        article.style.flex = "0 0 85%";
    
        for (var i = 0; i < menu_links.length; i++) {
            var link = menu_links[i];
            link.style.display = "block";
        }
    } else {
        menu_left.style.flex = "0 0 3%";
        menu_left.style.minWidth = "3vw";
        article.style.flex = "0 0 97%";
        for (var i = 0; i < menu_links.length; i++) {
            var link = menu_links[i];
            link.style.display = "none";
        }
    };
    
}