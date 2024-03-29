// Generated by CoffeeScript 1.8.0
var NHMobile, Promise,
  __slice = [].slice,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
  __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

Promise = (function() {
  Promise.when = function() {
    var args, num_uncompleted, promise, task, task_id, tasks, _fn, _i, _len;
    tasks = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
    num_uncompleted = tasks.length;
    args = new Array(num_uncompleted);
    promise = new Promise();
    _fn = function(task_id) {
      return task.then(function() {
        args[task_id] = Array.prototype.slice.call(arguments);
        num_uncompleted--;
        if (num_uncompleted === 0) {
          return promise.complete.apply(promise, args);
        }
      });
    };
    for (task_id = _i = 0, _len = tasks.length; _i < _len; task_id = ++_i) {
      task = tasks[task_id];
      _fn(task_id);
    }
    return promise;
  };

  function Promise() {
    this.completed = false;
    this.callbacks = [];
  }

  Promise.prototype.complete = function() {
    var callback, _i, _len, _ref, _results;
    this.completed = true;
    this.data = arguments;
    _ref = this.callbacks;
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      callback = _ref[_i];
      _results.push(callback.apply(callback, arguments));
    }
    return _results;
  };

  Promise.prototype.then = function(callback) {
    if (this.completed === true) {
      callback.apply(callback, this.data);
      return;
    }
    return this.callbacks.push(callback);
  };

  return Promise;

})();

NHMobile = (function(_super) {
  __extends(NHMobile, _super);

  NHMobile.prototype.process_request = function(verb, resource, data) {
    var promise, req;
    promise = new Promise();
    req = new XMLHttpRequest();
    req.addEventListener('readystatechange', function() {
      var successResultCodes, _ref;
      if (req.readyState === 4) {
        successResultCodes = [200, 304];
        if (_ref = req.status, __indexOf.call(successResultCodes, _ref) >= 0) {
          data = eval('[' + req.responseText + ']');
          console.log('data: ', data);
          return promise.complete(data);
        } else {
          new NHModal('data_error', 'Error while processing request', '<div class="block">The server returned an error while processing the request. Please check your input and resubmit</div>', ['<a href="#" data-action="close" data-target="data_error">Ok</a>'], 0, document.getElementsByTagName('body')[0]);
          return promise.complete(false);
        }
      }
    });
    req.open(verb, resource, true);
    if (data) {
      req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      req.send(data);
    } else {
      req.send();
    }
    return promise;
  };

  function NHMobile() {
    this.fullscreen_patient_info = __bind(this.fullscreen_patient_info, this);
    this.get_patient_info = __bind(this.get_patient_info, this);
    this.call_resource = __bind(this.call_resource, this);
    var self;
    this.urls = frontend_routes;
    self = this;
    NHMobile.__super__.constructor.call(this);
  }

  NHMobile.prototype.call_resource = function(url_object, data) {
    return this.process_request(url_object.method, url_object.url, data);
  };

  NHMobile.prototype.get_patient_info = function(patient_id, self) {
    return Promise.when(this.process_request('GET', this.urls.json_patient_info(patient_id).url)).then(function(server_data) {
      var data, patientDOB, patient_details, patient_name;
      data = server_data[0][0];
      patient_name = '';
      patient_details = '';
      if (data.full_name) {
        patient_name += " " + data.full_name;
      }
      if (data.gender) {
        patient_name += '<span class="alignright">' + data.gender + '</span>';
      }
      if (data.dob) {
        patientDOB = self.date_from_string(data.dob);
        patient_details += "<dt>DOB:</dt><dd>" + self.date_to_dob_string(patientDOB) + "</dd>";
      }
      if (data.location) {
        patient_details += "<dt>Location:</dt><dd>" + data.location;
      }
      if (data.parent_location) {
        patient_details += ',' + data.parent_location + '</dd>';
      } else {
        patient_details += '</dd>';
      }
      if (data.ews_score) {
        patient_details += "<dt class='twoline'>Latest Score:</dt><dd class='twoline'>" + data.ews_score + "</dd>";
      }
      if (data.other_identifier) {
        patient_details += "<dt>Hospital ID:</dt><dd>" + data.other_identifier + "</dd>";
      }
      if (data.patient_identifier) {
        patient_details += "<dt>NHS Number:</dt><dd>" + data.patient_identifier + "</dd>";
      }
      patient_details = '<dl>' + patient_details + '</dl><p><a href="' + self.urls['single_patient'](patient_id).url + '" id="patient_obs_fullscreen" class="button patient_obs">View Patient Observation Data</a></p>';
      new NHModal('patient_info', patient_name, patient_details, ['<a href="#" data-target="patient_info" data-action="close">Cancel</a>'], 0, document.getElementsByTagName('body')[0]);
      return document.getElementById('patient_obs_fullscreen').addEventListener('click', self.fullscreen_patient_info);
    });
  };

  NHMobile.prototype.fullscreen_patient_info = function(event) {
    var container, options, options_close, page;
    event.preventDefault();
    container = document.createElement('div');
    container.setAttribute('class', 'full-modal');
    options = document.createElement('p');
    options_close = document.createElement('a');
    options_close.setAttribute('href', '#');
    options_close.setAttribute('id', 'closeFullModal');
    options_close.innerText = 'Close popup';
    options_close.addEventListener('click', function() {
      return document.getElementsByTagName('body')[0].removeChild(document.getElementsByClassName('full-modal')[0]);
    });
    options.appendChild(options_close);
    container.appendChild(options);
    page = document.createElement('iframe');
    page.setAttribute('src', event.srcElement.getAttribute('href'));
    container.appendChild(page);
    return document.getElementsByTagName('body')[0].appendChild(container);
  };

  return NHMobile;

})(NHLib);

if (!window.NH) {
  window.NH = {};
}

if (typeof window !== "undefined" && window !== null) {
  window.NH.NHMobile = NHMobile;
}
