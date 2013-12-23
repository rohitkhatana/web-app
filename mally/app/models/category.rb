class Category
  include Mongoid::Document
  field :categoryName, type: String

  embedded_in :mall
end
