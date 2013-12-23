class Mall
  include Mongoid::Document
  field :name, type: String 
  field :cityname, type: String   
  #default type of an mongoid field is string
  #so we can also skip type declration on String
  embeds_many :categories 
end
