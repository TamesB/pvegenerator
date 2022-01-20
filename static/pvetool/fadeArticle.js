$(function() {
    $('#main .layerOneInner .article .article_content').css('display', 'none');
    $('#main .layerOneInner .article .article_content').fadeIn(100);
});

$(window).on('beforeunload', function() {
    $('#main .layerOneInner .article .article_content').fadeOut(100);
    $('#main .layerOneInner .article .popup-wrapper').fadeOut(100);
    $('#main .layerOneInner .article .loader').delay(500).fadeIn(100);
});