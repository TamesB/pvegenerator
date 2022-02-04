$(window).on('beforeunload', function() {
    $('#main .layerOneInner .article .article_content').fadeOut(100);
    $('#main .layerOneInner .article .popup-wrapper').fadeOut(100);
    $('#main .layerOneInner .article .loader').delay(500).fadeIn(100).delay(5000).fadeOut(100);
});