var hamburger = document.getElementById("hamburger");
var close_menu = document.getElementById("x_menu_button_1");
var menu_left = document.getElementById("menu_left");
var menu_links = document.getElementsByClassName("menu_link");
var article = document.getElementById("article");

hamburger.addEventListener("click", function() {
    this.classList.toggle("active")
    toggle_menu(this, menu_links, article, menu_left, close_menu);

})

close_menu.addEventListener("click", function() {
    hamburger.classList.toggle("active")
    toggle_menu(hamburger, menu_links, article, menu_left, close_menu);
})

function toggle_menu(element, menu_links, article, menu_left, close_menu) {
    if (element.classList.contains("active")) {
        menu_left.style.flex = "0 0 12%;"
        menu_left.style.minWidth = "12vw";
        article.style.flex = "0 0 88%";
    
        for (var i = 0; i < menu_links.length; i++) {
            var link = menu_links[i];
            link.style.display = "block";
        }

        close_menu.style.display = "block";

    } else {
        menu_left.style.flex = "0 0 2%";
        menu_left.style.minWidth = "40px";
        article.style.flex = "0 0 98%";
        for (var i = 0; i < menu_links.length; i++) {
            var link = menu_links[i];
            link.style.display = "none";
        }

        close_menu.style.display = "none";
    };
    
}