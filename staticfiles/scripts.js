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
    
     $('.item[data-value=""]').remove();
});
