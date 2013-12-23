class Offer
  include Mongoid::Document

  field :category, type: String
  field :description, type: String

end
