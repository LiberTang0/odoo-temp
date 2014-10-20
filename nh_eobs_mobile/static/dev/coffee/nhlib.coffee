# NHLib handles utilities that make working with Odoo easier
class NHLib

 # date format taken from odoo
 @date_format = '%Y-%m-%d H:M:S'

 constructor: () ->

   # version of lib
   @version = '0.0.1'

 date_from_string: (date_string) =>

   # return date for string
   return new Date(date_string)

 date_to_string: (date) =>

   # return date in string format
   return date.getFullYear() + "-" +  @leading_zero(date.getMonth() + 1) + "-" + @leading_zero(date.getDate()) + " " + @leading_zero(date.getHours()) + ":" + @leading_zero(date.getMinutes()) + ":" + @leading_zero(date.getSeconds())

 get_timestamp: () =>

   # return proper seconds based unix timestamp instead of milliseconds based one which is JS default
   return Math.round(new Date().getTime()/1000);

 leading_zero: (date_element) =>

   # add a zero string to the date and get the last two digits - if date_element is double digit then will return them else it with leading zero
   return ("0" + date_element).slice(-2)
   
module?.exports.NHLib = NHLib
window?.NH = {}
window?.NH.NHLib = NHLib

