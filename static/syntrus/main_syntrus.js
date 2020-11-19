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

     $('option[value=""]').remove();


});


/* Tooltip Info Bubble */
const template = document.createElement('template');
template.innerHTML = `
  <style>
    .tooltip-container {
      display: inline-block;
      position: relative;
      z-index: 2;
    }

    .cancel {
      display: none;
    }

    svg {
      width: 0.7em;
      cursor: pointer;
    }

    .notify-container {
      position: absolute;
      bottom: 125%;
      z-index: 9;
      width: 300px;
      background: white;
      box-shadow: 5px 5px 10px rgba(0,0,0,.1);
      font-size: .8em;
      font-family: 'Montserrat';
      color: black;
      border-radius: 1.6em;
      padding: 1em;
      transform: scale(0);
      transform-origin: bottom left;
      transition: transform .5s cubic-bezier(0.860, 0.000, 0.070, 1.000);
    }
  </style>
  <div class="tooltip-container">
    <svg xmlns="http://www.w3.org/2000/svg" class="alert" viewBox="0 0 100 100">
      <g id="tooltip-button" transform="translate(-653.639 -409.462)">
        <circle id="Ellipse_1" data-name="Ellipse 1" cx="50" cy="50" r="50" transform="translate(653.639 409.462)" fill="#1e3cff"/>
        <ellipse id="Ellipse_2" data-name="Ellipse 2" cx="7.32" cy="7.5" rx="7.32" ry="7.5" transform="translate(696.182 479.296)" fill="#fff"/>
        <path id="Path_1" data-name="Path 1" d="M10.082,0h18L22.2,39.69H16.381Z" transform="translate(685 429)" fill="#fff"/>
      </g>
    </svg>
    <svg xmlns="http://www.w3.org/2000/svg" class="cancel" viewBox="0 0 100 100">
      <g id="tooltip-x-button" transform="translate(-511 -412)">
        <circle id="Ellipse_3" data-name="Ellipse 3" cx="50" cy="50" r="50" transform="translate(511 412)" fill="#1e3cff"/>
        <rect id="Rectangle_2" data-name="Rectangle 2" width="68" height="12" transform="translate(588.284 442.201) rotate(135)" fill="#fff"/>
        <rect id="Rectangle_1" data-name="Rectangle 1" width="68" height="12" transform="translate(540.201 433.716) rotate(45)" fill="#fff"/>
      </g>
    </svg>
    <div class="notify-container">
      <slot name="message" />
    </div>
  </div>

  
`;

class PopupNotify extends HTMLElement {
  constructor () {
    super();
    this.attachShadow({mode: 'open'});
    this.shadowRoot.appendChild(template.content.cloneNode(true));
  }

  tooltip(expandState) {
    const tooltip = this.shadowRoot.querySelector('.notify-container');
    const alert = this.shadowRoot.querySelector('.alert');
    const cancel = this.shadowRoot.querySelector('.cancel');

    if (expandState == true) {
      tooltip.style.transform = 'scale(1)'
      alert.style.display = 'none'
      cancel.style.display = 'block'
      expandState = false;
    } else {
      tooltip.style.transform = 'scale(0)'
      alert.style.display = 'block'
      cancel.style.display = 'none'
      expandState = true;
    }
  }

  connectedCallback() {
    this.shadowRoot.querySelector('.alert').addEventListener('click', () => {
      this.tooltip(true)
    });
    this.shadowRoot.querySelector('.cancel').addEventListener('click', () => {
      this.tooltip(false)
    });
  }
}

window.customElements.define('popup-notify', PopupNotify)
/* End Tooltip object */