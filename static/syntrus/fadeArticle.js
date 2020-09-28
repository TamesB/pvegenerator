$(function() {
    $('#main .layerOneInner .article .article_content').css('display', 'none');
    $('#main .layerOneInner .article .article_content').fadeIn(200);
});

$(window).on('beforeunload', function() {
    $('#main .layerOneInner .article .article_content').fadeOut(200);
    $('#main .layerOneInner .article .popup-wrapper').fadeOut(200);
    $('#main .layerOneInner .article .loader').delay(500).fadeIn(200);
});