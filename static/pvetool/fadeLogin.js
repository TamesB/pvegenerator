$(function() {
    $('.centered_login .login_box').css('display', 'none');
    $('.centered_login .login_box').fadeIn(200);
});

$(window).on('beforeunload', function() {
    $('.centered_login .login_box').fadeOut(200);
    $('.centered_login .loader').delay(500).fadeIn(200);
});