$(document).ready(function(){
    $('.ui.checkbox')
        .checkbox();
  
     $('.ui.dropdown') 
        .dropdown();
     
     $('select.dropdown')
       .dropdown();
    
     $('.ui.modal')
       .modal('show')
     ;

     $('.ui.long.modal')
       .modal('show')
     ;
     
     $('.ui.longer.modal')
       .modal('show')
     ;
     
     $('.message .close')
       .on('click', function() {
         $(this)
           .closest('.message')
           .transition('fade')
         ;
       })
     ;
    
     $('.item[data-value=""]').innerHTML = "Kiezen..."
});
var win = $(this); //this = window
if (win.width()< 900) { $('#menu').removeClass('visible'); }
if (win.width()> 900) { $('#menu').addClass('visible'); }

 $(window).on('resize', function(){
  var win = $(this); //this = window
  if (win.width()< 900) { $('#menu').removeClass('visible'); }
  if (win.width()> 900) { $('#menu').addClass('visible'); }
});