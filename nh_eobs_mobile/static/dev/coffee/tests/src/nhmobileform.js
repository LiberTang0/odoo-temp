// Generated by CoffeeScript 1.8.0
var NHMobileForm,
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

NHMobileForm = (function(_super) {
  __extends(NHMobileForm, _super);

  function NHMobileForm() {
    var input, _fn, _i, _len, _ref, _ref1;
    this.form = (_ref = document.getElementsByTagName('form')) != null ? _ref[0] : void 0;
    _ref1 = this.form.elements;
    _fn = function() {
      switch (input.localName) {
        case 'input':
          switch (input.type) {
            case 'number':
              return input.addEventListener('change', function(event) {
                event.preventDefault();
                return console.log('validate');
              });
            case 'submit':
              return input.addEventListener('click', function(event) {
                event.preventDefault();
                return console.log('submit');
              });
          }
          break;
        case 'select':
          return input.addEventListener('change', function(event) {
            event.preventDefault();
            return console.log('trigger');
          });
      }
    };
    for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
      input = _ref1[_i];
      _fn();
    }
  }

  NHMobileForm.prototype.validate = function(event) {
    event.preventDefault();
    return console.log('validate');
  };

  NHMobileForm.prototype.trigger_actions = function(event) {
    event.preventDefault();
    return console.log('trigger');
  };

  NHMobileForm.prototype.submit = function(event) {
    event.preventDefault();
    return console.log('submit');
  };

  return NHMobileForm;

})(NHMobile);

if (typeof module !== "undefined" && module !== null) {
  module.exports.NHMobileForm = NHMobileForm;
}

if (typeof window !== "undefined" && window !== null) {
  window.NH = {};
}

if (typeof window !== "undefined" && window !== null) {
  window.NH.NHMobileForm = NHMobileForm;
}
