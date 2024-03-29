// Generated by CoffeeScript 1.8.0
var NHModal,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

NHModal = (function() {
  function NHModal(id, title, content, options, popupTime, el) {
    var cover, dialog, self;
    this.id = id;
    this.title = title;
    this.content = content;
    this.options = options;
    this.popupTime = popupTime;
    this.el = el;
    this.handle_button_events = __bind(this.handle_button_events, this);
    this.calculate_dimensions = __bind(this.calculate_dimensions, this);
    this.create_dialog = __bind(this.create_dialog, this);
    self = this;
    dialog = this.create_dialog(self, this.id, this.title, this.content, this.options);
    cover = document.createElement('div');
    cover.setAttribute('class', 'cover');
    cover.setAttribute('id', 'cover');
    cover.setAttribute('data-action', 'close');
    cover.setAttribute('data-target', this.id);
    cover.style.height = (el.clientHeight * 1.5) + 'px';
    cover.addEventListener('click', self.handle_button_events);
    this.el.appendChild(cover);
    this.el.appendChild(dialog);
    this.calculate_dimensions(dialog, dialog.getElementsByClassName('dialogContent')[0], this.el);
  }

  NHModal.prototype.create_dialog = function(self, popup_id, popup_title, popup_content, popup_options) {
    var container, content, dialog_content, dialog_div, dialog_header, dialog_options, header, options;
    dialog_div = function(id) {
      var div;
      div = document.createElement('div');
      div.setAttribute('class', 'dialog');
      div.setAttribute('id', id);
      return div;
    };
    dialog_header = function(title) {
      var header;
      header = document.createElement('h2');
      header.innerHTML = title;
      return header;
    };
    dialog_content = function(message) {
      var content;
      content = document.createElement('div');
      content.setAttribute('class', 'dialogContent');
      content.innerHTML = message;
      return content;
    };
    dialog_options = function(self, buttons) {
      var button, option_list, _fn, _i, _len;
      option_list = document.createElement('ul');
      switch (buttons.length) {
        case 1:
          option_list.setAttribute('class', 'options one-col');
          break;
        case 2:
          option_list.setAttribute('class', 'options two-col');
          break;
        case 3:
          option_list.setAttribute('class', 'options three-col');
          break;
        case 4:
          option_list.setAttribute('class', 'options four-col');
          break;
        default:
          option_list.setAttribute('class', 'options one-col');
      }
      _fn = function(self) {
        var option_button, _ref;
        option_button = document.createElement('li');
        option_button.innerHTML = button;
        if ((_ref = option_button.getElementsByTagName('a')) != null) {
          _ref[0].addEventListener('click', self.handle_button_events);
        }
        return option_list.appendChild(option_button);
      };
      for (_i = 0, _len = buttons.length; _i < _len; _i++) {
        button = buttons[_i];
        _fn(self);
      }
      return option_list;
    };
    container = dialog_div(popup_id);
    header = dialog_header(popup_title);
    content = dialog_content(popup_content);
    options = dialog_options(self, popup_options);
    container.appendChild(header);
    container.appendChild(content);
    container.appendChild(options);
    return container;
  };

  NHModal.prototype.calculate_dimensions = function(dialog, dialog_content, el) {
    var available_space, margins, max_height, top_offset;
    margins = 80;
    available_space = function(dialog, el) {
      var dialog_header_height, dialog_options_height, el_height, _ref, _ref1, _ref2, _ref3, _ref4, _ref5;
      dialog_header_height = (_ref = dialog.getElementsByTagName('h2')) != null ? (_ref1 = _ref[0]) != null ? _ref1.clientHeight : void 0 : void 0;
      dialog_options_height = (_ref2 = dialog.getElementsByClassName('options')) != null ? (_ref3 = _ref2[0]) != null ? (_ref4 = _ref3.getElementsByTagName('li')) != null ? (_ref5 = _ref4[0]) != null ? _ref5.clientHeight : void 0 : void 0 : void 0 : void 0;
      el_height = el.clientHeight;
      return el_height - ((dialog_header_height + dialog_options_height) + (margins * 2));
    };
    max_height = available_space(dialog, el);
    top_offset = el.offsetTop + margins;
    dialog.style.top = top_offset + 'px';
    dialog.style.display = 'inline-block';
    if (max_height) {
      dialog_content.style.maxHeight = max_height + 'px';
    }
  };

  NHModal.prototype.handle_button_events = function(event) {
    var cover, dialog_id, submit_event;
    switch (event.srcElement.getAttribute('data-action')) {
      case 'close':
        event.preventDefault();
        dialog_id = document.getElementById(event.srcElement.getAttribute('data-target'));
        cover = document.getElementById('cover');
        dialog_id.parentNode.removeChild(cover);
        return dialog_id.parentNode.removeChild(dialog_id);
      case 'submit':
        event.preventDefault();
        submit_event = new CustomEvent('post_score_submit', {
          'detail': event.srcElement.getAttribute('data-ajax-action')
        });
        document.dispatchEvent(submit_event);
        dialog_id = document.getElementById(event.srcElement.getAttribute('data-target'));
        cover = document.getElementById('cover');
        dialog_id.parentNode.removeChild(cover);
        return dialog_id.parentNode.removeChild(dialog_id);
      case 'partial_submit':
        event.preventDefault();
        submit_event = new CustomEvent('partial_submit', {
          'detail': {
            'action': event.srcElement.getAttribute('data-ajax-action'),
            'target': event.srcElement.getAttribute('data-target')
          }
        });
        return document.dispatchEvent(submit_event);
    }
  };

  return NHModal;

})();

if (!window.NH) {
  window.NH = {};
}

if (typeof window !== "undefined" && window !== null) {
  window.NH.NHModal = NHModal;
}
